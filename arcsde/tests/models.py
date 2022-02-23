
import uuid
import django.db.models
from arcsde import models

MAX_INT = 0xffffffff//2  # Postgre uses 4-byte integer with max value 2147483647

def mock_objectid():
    """ Return mock values for objectid so SDE models can be created in test fixtures """
    return uuid.uuid1().time_low%MAX_INT

def mock_globalid():
    """ Return mock values for globalid so SDE models can be created in test fixtures """
    return str(uuid.uuid4())

def create_sde_feature(model_class, **kwargs):
    """ Create an SDE feature instance suitable for testing, for given ArcSdeFeature model_class """
    return model_class.objects.create(objectid=mock_objectid(),
                                      globalid=mock_globalid(),
                                      **kwargs)


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
    class Meta:
        app_label = 'arcsde_tests'
        db_table = 'sde_feature'

    sde_attachments = models.ArcSdeAttachments()



class SdePointFeature(MockSdeIdsMixin, models.ArcSdePointMixin, models.AbstractArcSdeFeature):
    class Meta:
        app_label = 'arcsde_tests'
        db_table = 'sde_point_feature'


class SdeGeomFeature(MockSdeIdsMixin, models.ArcSdeGeometryMixin, models.AbstractArcSdeFeature):
    class Meta:
        app_label = 'arcsde_tests'
        db_table = 'sde_geom_feature'
