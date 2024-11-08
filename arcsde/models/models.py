"""
SDE feature models
@author: powderflask

Defines abstract base classes and business logic for Arc SDE feature models.
These models are always "unmanaged" (schema is managed by Arc).
Models can be backed directly by the feature table, but more usually by an "_evw" view exposing only active features.
To allow switching between table-backed and evw view-backed models:
    - always define model.Meta.db_table = sde_db_table('base_table_name')
    - define settings.SDE_USE_EVW = False to back models directly with a db table.
"""
import logging

from django.db import models, connection
from django.utils import timezone
from arcsde import settings, tz
from arcsde.models import managers, fields

logger = logging.getLogger('arcsde')


def sde_db_table(base_table_name, use_evw=settings.SDE_USE_EVW):
    """
    Arc SDE tables have a "base table" that uses archiving and an "EVW" view that presents only current records
    Models can be configured to run from either of these data sources using settings.SDE_USE_EVW
    SDE models use this fn to select which relation to draw their data from.
    """
    if use_evw:
        return "%s_evw"%base_table_name
    else:
        return base_table_name


def sde_base_db_table(table_name, use_evw=settings.SDE_USE_EVW):
    """
    Reverse the logic above so we can get back the base table name (used by attachments)
    Why not just have the report model class store the base table name?  That'd be nice, but...
    Django does not allow arbitrary attributes to be added to Meta, so nowhere DRY to store it!
    """
    if use_evw:
        return table_name[:-4]
    else:
        return table_name


def pg_table_owner(table_name):
    """
    Return the  username of the table owner, required by some SDE functions
    Note: this is for Postgre DB only, and should really be integrated into a DB backend  ** sigh **
    """
    QUERY = """
        select u.usename
        from information_schema.tables t
        join pg_catalog.pg_class c on (t.table_name = c.relname)
        join pg_catalog.pg_user u on (c.relowner = u.usesysid)
        where t.table_name=%s;
    """
    with connection.cursor() as cursor:
        cursor.execute(QUERY, [table_name, ])
        return cursor.fetchone()[0]


class AbstractArcSdeBase(models.Model):
    """
        Adds base SDE fields and SdeManager so queries on SDE models are filtered correctly.
    """
    class Meta:
        abstract = True
        managed = False
        base_manager_name = 'objects'  # use ArcSdeManager as the base_manager for related SDE objects

    # PK'ish: attach models and other features may use globalid to form FK'ish relations!! Set unique=True to simulate
    globalid = models.CharField(max_length=38, unique=True, editable=False)

    # If using base tables, we need the gdb_to_date to filter results.
    if not settings.SDE_USE_EVW:
        gdb_to_date = fields.ArcSdeDateTimeField(editable=False)

    # Selects only the "active" (non-archived) records
    objects = managers.ArcSdeManager()
    annotated = managers.AnnotatedArcSdeManager()  # Use for queries that require common attributes


class ArcSdeObjectidMixin(models.Model):
    """
        Adds 'objectid' field as the primary key -- used by most SDE models
    """
    # NOTE :: "All django models must have one field marked as the primary_key"
    #    This mixin satisfies this reasonable constraint by "faking" a primary_key designation on a unique field.
    #    objectid MUST exist as a unique field in every SdeBase table
    #    This field is most often used to form FK-like relations, although globalid is also commonly used.
    objectid = models.AutoField(primary_key=True, editable=False)

    class Meta:
        abstract = True


class ArcSdeFeatureCreationMixin(models.Model):
    """
        A mixin for  create an ArcSdeFeature models that need to create new instances.
        Ideally 3rd party code should not create SDE feature data -- resist pressure to do so!
        But in cases where it is unavoidable, we need to fake values for the SDE globalid and objectid keys
        Test cases for models that use this mixin should set globalid=uuid.uuid4() when creating test fixture instances
            - see arcsde.tests.models for convenience method for creating SDE test fixture data
    """
    # SDE DB procs to fetch next keys for new features
    NEXT_GLOBALID = 'next_globalid'
    NEXT_OBJECTID = 'next_rowid'

    class Meta:
        abstract = True

    def save(self,*args, **kwargs):
        """ Set values for globalid and objectid keys before saving new records """
        if hasattr(self, 'globalid') and not self.globalid:
            self.globalid = models.expressions.RawSQL(f'{self.NEXT_GLOBALID}()', params=())
        if hasattr(self, 'objectid') and not self.objectid:
            self.objectid = models.expressions.RawSQL(*self.next_objectid_call())
        return super().save(*args, **kwargs)

    @classmethod
    def get_next_globalid(cls):
        """ Get the next SDE globalid """
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {cls.NEXT_GLOBALID}()", [])
            return cursor.fetchone()[0]

    @classmethod
    def next_objectid_call(cls, owner=None, table=None):
        """ Return the dB proc call, as a string, and parameter list, to get the next SDE objectid for given table """
        table = table or cls._meta.db_table
        owner = owner or pg_table_owner(table)  # why does Arc need the table owner to compute next ID?  why Arc, why?
        return f"{cls.NEXT_OBJECTID}(%s, %s)", (owner, table)

    @classmethod
    def get_next_objectid(cls, owner=None, table=None):
        """ Get the next SDE objectid for given table """
        fn_call, params = cls.next_objectid_call(owner, table)
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {fn_call}", params)
            return cursor.fetchone()[0]


class SdeVersionField(fields.ArcSdeDateTimeField):
    def formfield(self, **kwargs):
        """ Define a hidden DateTime field used as versioning mechanism for concurrency detection. """
        from arcsde import forms
        defaults = {'form_class': forms.SdeVersionField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class ArcSdeRevisionFieldsMixin(models.Model):
    """
        Fields used to track revision information on SDE models.
    """
    created_user = models.CharField(max_length=255, blank=True, null=True, editable=False,
                                    verbose_name='Created By'
                                    )
    created_date = fields.ArcSdeDateTimeField(blank=True, null=True, editable=False,
                                    verbose_name='Created On'
                                    )
    last_edited_user = models.CharField(max_length=255, blank=True, null=True,
                                    verbose_name='Last Modified By'  # set by custom save() method on SdeModelForm
                                    )
    last_edited_date = SdeVersionField(blank=True, null=True,
                                    verbose_name='Date Last Modified'
                                    )

    class Meta:
        abstract = True

    SDE_EDITED_BY_ANNOTATION = managers.ArcSdeQuerySet.SDE_EDITED_BY_ANNOTATION
    EDIT_TRACKING_ERROR = f'''SDE feature ({{feature}}) saved without {SDE_EDITED_BY_ANNOTATION} annotation on instance.
    Add .set_edited_by(username) to queryset to track requester's username in SDE last_edited_user field.'''

    LAST_EDITED_DATE_BASE = 'last_edited_date'
    LAST_EDITED_USER_BASE = 'last_edited_user'
    last_edited_date_field = LAST_EDITED_DATE_BASE
    last_edited_user_field = LAST_EDITED_USER_BASE

    def get_last_edited_date(self):
        """ Allow sub-classes to override the field used to store last-edited_date """
        date = getattr(self, self.last_edited_date_field, None)      # ideally, this models last edited date
        base_date = getattr(self, self.LAST_EDITED_DATE_BASE, None)  # but base date as a fallback
        return date or base_date or timezone.datetime.fromordinal(1) # or -infinity if no dates are sets.

    def get_last_edited_user(self):
        """ Allow sub-classes to override the field used to store last-edited_user """
        user = getattr(self, self.last_edited_user_field, None)
        base_user = getattr(self, self.LAST_EDITED_USER_BASE, None)
        return user or base_user or "None"

    def update_edit_tracking(self, username=None):
        """
            Call to update the last_edited_user / date fields.
            Normal case: feature queryset .set_edited_by(username) to automated edit tracking on save,
            Optionally: pass username directly, e.g., for bulk updates where save logic is skipped.
            Always update the BASE fields - DB trigger determines if the associated *_field_* gets updated.
            Look for annotation that clients must set to enable edit tracking - log error if it is not provided.
        """
        username = username or getattr(self, self.SDE_EDITED_BY_ANNOTATION, None)
        if not username:
            msg = self.EDIT_TRACKING_ERROR.format(feature=repr(self))
            if settings.SDE_EDIT_TRACKING_ENFORCE:
                if settings.settings.DEBUG and not settings.UNIT_TESTING:
                    raise Exception(msg)
                else:
                    logger.warning(msg)
            else:
                logger.debug(msg)
            username = settings.SDE_EDIT_TRACKING_DEFAULT_USERNAME

        if not self.pk and isinstance(self, ArcSdeFeatureCreationMixin):
            self._set_creation_fields(username)
        setattr(self, self.LAST_EDITED_USER_BASE, username)
        setattr(self, self.LAST_EDITED_DATE_BASE, timezone.now())

    def _set_creation_fields(self, username):
        """ For rare occassions when SDE features are created.  See ArcSdeFeatureCreationMixin for warnings. """
        if self.pk or not isinstance(self, ArcSdeFeatureCreationMixin):
            return
        self.created_user = username
        self.created_date = timezone.now()

    def get_report_version_info(self):
        return {
            'created_by': self.created_user,
            'created_on': self.created_date,
            'edited_by' : self.get_last_edited_user(),
            'edited_on' : self.get_last_edited_date()
        }

    def was_created_by(self, user):
        """ Return True iff this report was likely created by the given user """
        # "likely" because there is no direct relation to created user, only the SDE text field storing their username
        return self.created_user.lower() == user.username.lower()

    def was_last_edited_by(self, user):
        """ Return True iff this report was likely last edited by the given user """
        # "likely" because there is no direct relation to created user, only the SDE text field storing their username
        return self.get_last_edited_user().lower() == user.username.lower()


    def save(self, *args, **kwargs):
        """ Save edit tracking fields for each new revision  - client MUST set_edited_by(u) on qs for this to work """
        if settings.SDE_EDIT_TRACKING:
            self.update_edit_tracking()
        super().save(*args, **kwargs)


class AbstractArcSdeFeature(ArcSdeObjectidMixin, ArcSdeRevisionFieldsMixin, AbstractArcSdeBase):
    """
        Abstract base class for Arc SDE feature models
    """
    class Meta:
        abstract = True
        managed = False


class ArcSdeGeometryMixin(models.Model):
    """
        Conceptually add an arcsde.st_geometry field to the model.  Use only with models based on AbstractArcSdeFeature
        Unfortunately, geo-django can't interpret this data, and we don't want to tamper with it - so use carefully.
        The SdeManager() can annotate the model with shape_text (WKT) and shape_geos (WKB) fields derived from shape.
    """
    shape = fields.ArcSdeGeometryField(blank=True, null=True, editable=False)

    class Meta:
        abstract = True

    has_shape = True
    is_point = False


class ArcSdeLineMixin(models.Model):
    """
        Conceptually add an arcsde.st_line field to the model.  Use only with models based on AbstractArcSdeFeature
        See notes in ArcSdeGeometryMixin above
    """
    shape = fields.ArcSdeLineField(blank=True, null=True, editable=False)

    class Meta:
        abstract = True

    has_shape = True
    is_point = False


class ArcSdePointMixin(models.Model):
    """
        Conceptually add an arcsde.st_point field to the model.  Use only with models based on AbstractArcSdeFeature
        See notes in ArcSdeGeometryMixin above
    """
    shape = fields.ArcSdePointField(blank=True, null=True, editable=False)

    class Meta:
        abstract = True

    has_shape = True
    is_point = True


class ArcSdeArchiveMixin(models.Model):
    """ Mixin SDE archive fields and an active record manager """
    # objectid = models.IntegerField(unique=False, editable=False)  # django forbids 2 abstract base models to both define same field.

    gdb_archive_oid = models.IntegerField(primary_key=True)

    if settings.SDE_USE_EVW:  # be sure not to double add field
        gdb_to_date = fields.ArcSdeDateTimeField(editable=False)

    class Meta:
        abstract = True
