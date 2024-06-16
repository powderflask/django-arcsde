"""
    Test suite for SDE Model Fields
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from django.test import TestCase
from django.utils import timezone

from arcsde import tz, settings
from . import models


class ArcSdeDateTimeFieldTests(TestCase):
    def test_naive_datetime(self):
        """ Test that a naive datetime is converted back to local time when read. """
        dt = timezone.now()  # naive timezone (settings.USE_TZ=False) in local TZ, settings.TIME_ZONE
        self.assertEqual(dt.tzinfo, None)
        instance = models.SdeFeatureModel.objects.create(dt=dt)
        self.assertEqual(dt.hour, instance.dt.hour)
        instance2 = models.SdeFeatureModel.objects.first()
        self.assertEqual(instance2.dt.tzinfo, ZoneInfo(settings.TIME_ZONE))
        self.assertEqual(dt.hour, instance2.dt.hour)

    def test_aware_datetime(self):
        """ Test that an aware datetime is correctly converted to local time. """
        dt = datetime.now(tz=ZoneInfo(settings.SDE_DB_TIME_ZONE))
        instance = models.SdeFeatureModel.objects.create(dt=dt)
        self.assertEqual(dt.hour, instance.dt.hour)  # Note: keeps its timezone aware time
        instance2 = models.SdeFeatureModel.objects.first()
        self.assertEqual(instance2.dt.tzinfo, ZoneInfo(settings.TIME_ZONE))
        self.assertNotEqual(dt.hour, instance2.dt.hour)
        self.assertEqual(dt, tz.localize(instance2.dt))
