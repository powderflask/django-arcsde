
import uuid

import django.db.models
import django.forms
from django.utils import timezone

from arcsde import models, forms
from arcsde.tests.db import CREATE

MAX_INT = 0xffffffff//2  # Postgre uses 4-byte integer with max value 2147483647

def mock_objectid():
    """ Return mock values for objectid so SDE models can be created in test fixtures """
    return uuid.uuid1().time_low%MAX_INT

def mock_globalid():
    """ Return mock values for globalid so SDE models can be created in test fixtures """
    return str(uuid.uuid4())

def create_sde_feature(model_class, **kwargs):
    """ Create an SDE feature instance suitable for testing, for given ArcSdeFeature model_class """
    instance = model_class(objectid=mock_objectid(),
                           globalid=mock_globalid(),
                           **kwargs)
    setattr(instance, models.ArcSdeRevisionFieldsMixin.SDE_EDITED_BY_ANNOTATION, 'arcsde_test_fixture')
    instance.save()
    return instance


class MockSdeIdsMixin(django.db.models.Model):

    class Meta:
        abstract = True

    def save(self,*args, **kwargs):
        """ Set values for globalid and objectid keys before saving new records """
        if not self.globalid:
            self.globalid = mock_globalid()
        # let test DB supply objectid auto-increment value
        return super().save(*args, **kwargs)


class SdeFeatureModel(MockSdeIdsMixin, models.ArcSdeAttachmentsMixin, models.AbstractArcSdeFeature):
    some_attr = django.db.models.CharField(verbose_name='some_attr',  blank=True, default='', max_length=50)
    dt = models.ArcSdeDateTimeField(verbose_name='SDE DateTime', default=timezone.now)

    class Meta:
        app_label = 'arcsde_tests'
        managed = False  # see db.create_tables_for_unmanaged_test_models
        db_table = 'sde_feature'

    sde_attachments = models.ArcSdeAttachments()


SdeFeatureModel_ddl = """
CREATE TABLE "sde_feature"
("objectid" integer PRIMARY KEY AUTOINCREMENT,
"globalid" varchar(38) NOT NULL UNIQUE,
"some_attr" varchar(50) NULL,
"dt" timestamp without time zone NOT NULL,
"created_user" varchar(50) NULL,
"created_date" timestamp without time zone NULL,
"last_edited_user" varchar(50) NULL,
"last_edited_date" timestamp without time zone NULL);
"""

class SdeFeatureForm(forms.AbstractSdeForm):
    """ Critically, child form inherits version field from base form, used for concurrency check """
    class Meta:
        model = SdeFeatureModel
        fields = ('some_attr', )  # notice child form need not specify the version field - django will include it.


class SdeFeatureFormWithObjectid(SdeFeatureForm):
    objectid = django.forms.IntegerField(widget=django.forms.HiddenInput())

    class Meta(SdeFeatureForm.Meta):
        fields = ('some_attr', )


class SdeFeatureFormWithDateTime(SdeFeatureForm):
    class Meta(SdeFeatureForm.Meta):
        fields = ('dt', )


class SdePointFeature(MockSdeIdsMixin, models.ArcSdePointMixin, models.AbstractArcSdeFeature):
    class Meta:
        app_label = 'arcsde_tests'
        db_table = 'sde_point_feature'


class SdeGeomFeature(MockSdeIdsMixin, models.ArcSdeGeometryMixin, models.AbstractArcSdeFeature):
    class Meta:
        app_label = 'arcsde_tests'
        db_table = 'sde_geom_feature'
