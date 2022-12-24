"""
    Test suite for SDE base models / business logic
"""
from datetime import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model

from arcsde import models, tz
from .models import SdeFeatureModel, SdeGeomFeature, SdePointFeature

class TableNameTests(TestCase):

    def test_sde_table_names(self):
        """
        The sde_table name should have an _evw if the app is using Views rather than the base tables.
        The reverse name should be equal to the original
        """
        base_name = 'test_table_name'
        with self.settings(SDE_USE_EVW=False):
            table_name = models.sde_db_table(base_name, use_evw=False)
            self.assertEqual(base_name, table_name, "SDE table / view names not mapped")
           # reverse it
            self.assertEqual(base_name, models.sde_base_db_table(table_name, use_evw=False),
                             "SDE reverse table name not working.")

        with self.settings(SDE_USE_EVW=True):
            table_name = models.sde_db_table(base_name, use_evw=True)
            self.assertLess(len(base_name), len(table_name), "SDE table / view names not mapped")
           # reverse it
            self.assertEqual(base_name, models.sde_base_db_table(table_name, use_evw=True),
                             "SDE reverse table name not working.")


class BaseModelsTests(TestCase):

    def setUp(self):
        self.sde_feature = None
        self.user = None

    def tearDown(self):
        if self.sde_feature:
            self.sde_feature.delete()
        if self.user:
            self.user.delete()

    def _get_feature(self):
        if not self.sde_feature:
            self.sde_feature = SdeFeatureModel()
        return self.sde_feature

    def _get_user(self):
        if not self.user:
            self.user = get_user_model().objects.create(username='SomeUser', email='user@example.com', password='abc123')
        return self.user


class ArcSdeRevisionFieldsMixinTests(BaseModelsTests):
    def test_create_user(self):
        sde_feature = self._get_feature()
        user = self._get_user()
        setattr(sde_feature, sde_feature.SDE_EDITED_BY_ANNOTATION, user.username)
        sde_feature.save()
        self.assertEqual(sde_feature.last_edited_user, user.username)
        self.assertTrue(sde_feature.was_last_edited_by(user))

    def test_edit_user(self):
        sde_feature = self._get_feature()
        user = self._get_user()
        setattr(sde_feature, sde_feature.SDE_EDITED_BY_ANNOTATION, user.username)
        sde_feature.save()

        other_user = get_user_model().objects.create(username='AnotherUser', email='another@example.com', password='abc123')
        setattr(sde_feature, sde_feature.SDE_EDITED_BY_ANNOTATION, other_user.username)
        self.sde_feature.save()
        self.assertEqual(self.sde_feature.last_edited_user, other_user.username)
        self.assertTrue(self.sde_feature.was_last_edited_by(other_user))

    def test_version_info(self):
        then = datetime.now(tz=tz.LOCAL_TIME_ZONE)
        sde_feature = self._get_feature()
        user = self._get_user()
        setattr(sde_feature, sde_feature.SDE_EDITED_BY_ANNOTATION, user.username)
        sde_feature.save()
        now = datetime.now(tz=tz.LOCAL_TIME_ZONE)
        version_info = sde_feature.get_report_version_info()
        self.assertEqual(version_info['edited_by'], user.username)
        self.assertGreaterEqual(version_info['edited_on'], then)
        self.assertLessEqual(version_info['edited_on'], now)
        self.assertTrue('created_by' in version_info.keys() and 'created_on' in version_info.keys())


class AbstractArcSdeFeatureTests(BaseModelsTests):

    def test_attributes(self):
        sde_feature = self._get_feature()

        self.assertTrue(hasattr(sde_feature, 'globalid'), 'globalid unique key not found in SDE feature models.')
        self.assertTrue(hasattr(sde_feature, 'objectid'), 'objectid pk not found in SDE feature models.')
        # verify that objectid is the primary key field
        sde_feature.pk = 999
        self.assertEqual(sde_feature.pk, sde_feature.objectid, 'objectid attr is not the primary key field')
        # verify edit tracking logic
        setattr(sde_feature, sde_feature.SDE_EDITED_BY_ANNOTATION, 'some_user')
        sde_feature.update_edit_tracking()
        self.assertEqual(sde_feature.last_edited_user, 'some_user', 'update_edit_tracking not working.')

    def test_create(self):
        sde_feature = self._get_feature()
        sde_feature.save()
        self.assertIsNotNone(sde_feature.globalid, 'null globalid unique key in saved SDE feature model.')
        self.assertIsNotNone(sde_feature.objectid, 'null objectid pk in saved SDE feature model.')


class ArcSdeShapeMixinTests(BaseModelsTests):
    # Can't test any shape logic (e.g., lat/long, area, intersect) without a proper SDE database backing test suite :-(

    def test_point_mixin(self):
        sde_feature = SdePointFeature()
        self.assertTrue(sde_feature.has_shape)
        self.assertTrue(sde_feature.is_point)

    def test_geom_mixin(self):
        sde_feature = SdeGeomFeature()
        self.assertTrue(sde_feature.has_shape)
        self.assertFalse(sde_feature.is_point)
