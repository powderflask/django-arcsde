"""
Attachments to SDE features
@author: powderflask

Arc SDE feature attachments with a standard ArcSdeBase table defining
 the relation to the attached SDE model along with a content_type and binary data containing attachment.

To add the "attachment_set" RelatedManager + ArcSdeAttachmentsApi to any SDE model, simply add the descriptor:
    sde_attachments = arcsde.ArcSdeAttachments()

Also recommended, add the ArcSdeAttachmentsMixin to the sde feature model class:
    class MySdeFeature(ArcSdeAttachmentsMixin, AbstractArcSdeFeature):
        ...
        sde_attachments = arcsde.ArcSdeAttachments()
        ...
"""
import base64, functools
from django.db import models, connection
from django.urls import reverse
from django.utils.functional import cached_property

from arcsde.models import AbstractArcSdeBase, sde_db_table, sde_base_db_table
from arcsde.attachments.managers import SdeAttachmentManager


class AttachmentModelRegistry:
    """
        A registry of model classes with their related ConcreteSdeAttachModel
        Lookup by the related class or by its class.__name__
     """
    registry = {}

    class Entry:
        def __init__(self, related_class, attachments_model):
            self.related_class = related_class
            self.attachments_model = attachments_model

        def __str__(self):
            return self.attachments_model

    @staticmethod
    def _get_class_name(related_class):
        return related_class if isinstance(related_class, str) else related_class.__name__

    @classmethod
    def register(cls, related_class, attachments_model):
        """ related class may be a string (class.__name__) or the class itself """
        related_class_name = cls._get_class_name(related_class)
        cls.registry[related_class_name] = cls.Entry(related_class, attachments_model)

    @classmethod
    def get_related_model(cls, related_class):
        """ Return the related_class's model class (i.e., lookup related class by name) """
        related_class_name = cls._get_class_name(related_class)
        try:
            return cls.registry[related_class_name].related_class
        except KeyError:
            return None

    @classmethod
    def get_attachment_model(cls, related_class):
        """ Return the ConcreteSdeAttachModel for the given related class """
        related_class_name = cls._get_class_name(related_class)
        try:
            return cls.registry[related_class_name].attachments_model
        except KeyError:
            return None

    @classmethod
    def related_model_in_registry(cls, related_class):
        """ Return True iff related_class is in the registry """
        return cls.get_related_model(related_class) is not None

    @classmethod
    def all_attachment_related_models(cls):
        """ Return an iterable of all attachment-related models in the registry """
        return (v.related_class for v in cls.registry.values())


class AbstractSdeAttachModel(AbstractArcSdeBase):
    """
        Base class for Arc SDE __attach attachment tables.
        Use get_attachment_model class factory to build concrete attachment model classes.
        Sub-classes MUST supply the FK to the related model for the attachment:
        related_object = models.ForeignKey('RelatedModel', db_column='rel_globalid', to_field='globalid', db_constraint=False)
    """
    attachmentid = models.AutoField(primary_key=True, editable=False)
    related_object = None                            # FK to related model supplied by concrete sub-class...
    #rel_globalid = models.CharField(max_length=38)  #    rel_globalid defines FK to SDE model by ConcreteSdeAttachModel
    content_type = models.CharField(max_length=150)
    att_name = models.CharField(max_length=250)
    data_size = models.IntegerField()
    data = models.BinaryField(blank=True, null=True)

    class Meta:
        abstract = True

    objects = SdeAttachmentManager()

    @property
    def related_model_class(self):
        """ Model class of the related model to this attachment """
        return self._meta.get_field('related_object').related_model().__class__

    @property
    def related_pk(self):
        """ Allow for non-unique relations b/w attachment and related model, e.g in view """
        try:
            return self.related_object.pk
        except models.base.MultipleObjectsReturned:
            # Hack alert: handle failure when relation is non-unique (e.g., PatrolPlotPerCircuitVw)
            filter = {self._meta.get_field('related_object').target_field.name: self.related_object_id}
            return self.related_model_class.objects.filter(**filter).values_list('pk', flat=True).first()

    def get_base64_utf8_encoding(self):
        # Encode to get base-64 byte string, decode to UTF-8 for transmission over http
        return base64.b64encode(self.data).decode() if self.data else ''

    def get_data_URI(self):
        """
            Return suitable data URI for src attribute of html img tag
            see: https://en.wikipedia.org/wiki/Data_URI_scheme
        """
        return "data:%s;base64,%s"%(self.content_type, self.get_base64_utf8_encoding())

    def image_list_url(self):
        related_model = self.related_model_class.__name__
        app_label=self.related_model_class._meta.app_label
        return reverse('arcsde:attachments:images-list-ajax',
                        args=(app_label, related_model, self.related_pk)
                      )

    def caption_save_url(self):
        related_model = self.related_model_class.__name__
        app_label=self.related_model_class._meta.app_label
        return reverse('arcsde:attachments:caption-save-ajax',
                        args=(app_label, related_model, self.related_pk, self.pk)
                      )

    @classmethod
    def get_test_object(cls):
        test_red_dot=base64.b64decode("""
            iVBORw0KGgoAAAANSUhEUgAAAAUA
            AAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO
            9TXL0Y4OHwAAAABJRU5ErkJggg==""")
        return cls(content_type='image/png', data=test_red_dot, data_size=len(test_red_dot))


@functools.lru_cache()   # Avoid repeating DB introspection - the db table isn't going to suddenly appear :-)
def db_table_exists(table_name):
    """
        Return True iff given table or view name exits in DB.
    """
    return table_name in connection.introspection.table_names(include_views=True)

def get_attachment_model_db_table_name(related_model):
    # noinspection PyProtectedMember
    return sde_db_table('%s__attach'%sde_base_db_table(related_model._meta.db_table))

def get_attachment_model_name(related_model):
    return "%sAttachments"%related_model.__name__

def get_attachment_model(related_model, attachment_model_db_table_name=None):
    """
    Attachment Model Class Factory :  returns a concrete SdeAttachModel for the given related_model
    Attachment model classes are registered in AttachmentModelRegistry
    Usage Ex.: get_attachment_model(MySdePointFeatureModelClass) yields  SdeAttachModel class for 'my_point_feature_pt__attach'
    :param related_model: a django model class with a related __attach table
    :param attachment_model_db_table_name: optional DB table name for related_model attachments - defaults to SDE scheme
    :return: a django model class for the __attach table related to the related model or None
    """
    # noinspection PyProtectedMember
    cls_name = get_attachment_model_name(related_model)
    db_table_name = attachment_model_db_table_name or get_attachment_model_db_table_name(related_model)

    attachment_model = AttachmentModelRegistry.get_attachment_model(related_model)
    if attachment_model:
        return attachment_model
    elif not db_table_exists(db_table_name):
        return None  # no such related attachments exist, so there is no such model
    else:
        pass  # create the concrete django Model for identified attachments db_table

    class MetaSdeAttachModel(models.base.ModelBase):
        """
           Create the specific Concrete Attachment Model Class for the related model.
           Metaclass is needed so that ConcreteSdeAttachModel for different related_models are distinct.
        """
        def __new__(mcs, generic_name, bases, attrs):
            return super(MetaSdeAttachModel, mcs).__new__(mcs, cls_name, bases, attrs)

    class ConcreteSdeAttachModel(AbstractSdeAttachModel, metaclass=MetaSdeAttachModel):
        related_object = models.ForeignKey(related_model, related_name='attachment_set',
                                           db_column='rel_globalid', to_field='globalid',
                                           db_constraint=False, on_delete=models.CASCADE)

        class Meta:
            managed = False
            db_table = db_table_name

    AttachmentModelRegistry.register(related_model, ConcreteSdeAttachModel)

    return ConcreteSdeAttachModel


class ArcSdeAttachmentsApi:
    """
        Simple API for caching and access to common ArcSDE attachments queries and business logic
        Assumes there is a ConcreteSdeAttachModel for access to related model instances's attachment_set,
            if the instance has no attachments, methods return default "no attachments" values
        Usage:                my_attachments = ArcSdeAttachmentsApi(some_sde_feature_instance)
        OR using descriptor:  sde_attachments = ArcSdeAttachmentsDescriptor()
    """
    def __init__(self, related_instance):
        """ Create API for caching and access to related_instance.attachment_set """
        # assumes related_name from ConcreteSdeAttachModel.related_object is "attachment_set"
        self.instance = related_instance
        try:
            self.attachment_set = related_instance.attachment_set
        except AttributeError:
            self.attachment_set = None  # no attachments relation - be sure get_attachment_model has been called!

    @property
    def has_attachments(self):
        """ Return True iff this SDE feature has a related attachments Manager """
        return self.attachment_set is not None

    @property
    def exists(self):
        """ Return True iff this SDE feature has 1 or more related attachments """
        # use annotation from annotate_attachment_count if avaialble, or fallback to exists query
        return self.instance.attachment_count > 0 if hasattr(self.instance, 'attachment_count') else \
               self.attachment_set.exists() if self.has_attachments else False

    @cached_property
    def images(self):
        """ Return complete queryset of image attachments for this feature, or None """
        return self.attachment_set.all().sde_image_attachments() if self.has_attachments else None

    @cached_property
    def count(self):
        """ Return the number of attachments objects related to this feature """
        # use annotation from annotate_attachment_count if avaialble, or fallback to count query
        return self.instance.attachment_count if hasattr(self.instance, 'attachment_count') else \
               self.attachment_set.count() if self.has_attachments else False

    @cached_property
    def images_url(self):
        related_class_name = self.instance.__class__.__name__
        app_label = self.instance._meta.app_label
        return reverse('arcsde:attachments:images-list-ajax', args=( app_label, related_class_name, self.instance.pk)) \
            if self.has_attachments else None

    @property
    def attachments_model(self):
        return AttachmentModelRegistry.get_attachment_model(self.instance.__class__)


class ArcSdeAttachmentsMixin:
    """
        A simple mixin, primarily intended for features with an ArcSdeAttachmentsDescriptor
        Simply provides a default class property for the descriptor (for consistency) and a means of determining
            if the feature model class actually has a related attachments model, used to create Attach models on ready()
    """
    sde_attachments = None  # usually a ArcSdeAttachmentsApi injected by an ArcSdeAttachments() descriptor

    @classmethod
    def has_attachments(cls):
        """ Return True iff this SDE feature has a related attachments Manager """
        return cls.sde_attachments is not None
