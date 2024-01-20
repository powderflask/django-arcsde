"""
    Test suite for SDE Time Zone logic
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from django.test import TestCase

from arcsde import tz, settings


class TzTests(TestCase):
    def test_localize_naive(self):
        """ Test that a naive datetime is interpreted as UTC then converted to local time. """
        dt = datetime.now()
        self.assertEqual(dt.tzinfo, None)
        local = tz.localize(dt)
        self.assertEqual(local.tzinfo, ZoneInfo(settings.SDE_LOCAL_TIME_ZONE))
        self.assertNotEqual(dt.hour, local.hour)


    def test_localize_aware(self):
        """ Test that an aware datetime is interpreted correctly and converted to local time. """
        dt = datetime.now(tz=ZoneInfo('UTC'))
        self.assertEqual(dt.tzinfo, ZoneInfo('UTC'))
        local = tz.localize(dt)
        self.assertEqual(local.tzinfo, ZoneInfo(settings.SDE_LOCAL_TIME_ZONE))
        self.assertNotEqual(dt.hour, local.hour)

    def test_localize_local(self):
        """ Test that an already localized datetime is not altered by localization. """
        dt = datetime.now(tz=ZoneInfo(settings.SDE_LOCAL_TIME_ZONE))
        local = tz.localize(dt)
        self.assertEqual(local.tzinfo, ZoneInfo(settings.SDE_LOCAL_TIME_ZONE))
        self.assertEqual(dt, local)

    def test_delocalize_local(self):
        """ Test that a localized datetime is de-localized to SDE timezone. """
        dt = datetime.now(tz=ZoneInfo(settings.SDE_LOCAL_TIME_ZONE))
        sde = tz.delocalize(dt)
        self.assertEqual(sde.tzinfo, ZoneInfo(settings.TIME_ZONE))
        self.assertNotEqual(dt.hour, sde.hour)

    def test_delocalize_sde(self):
        """ Test that a datetime already in SDE timezone is unaltered by delocalization. """
        dt = datetime.now(tz=ZoneInfo(settings.TIME_ZONE))
        sde = tz.delocalize(dt)
        self.assertEqual(sde.tzinfo, ZoneInfo(settings.TIME_ZONE))
        self.assertEqual(dt, sde)

    def test_delocalize_naive(self):
        """ Test that a naive datetime is interpreted as UTC. """
        dt = datetime.now()
        self.assertEqual(dt.tzinfo, None)
        sde = tz.delocalize(dt)
        self.assertEqual(sde.tzinfo, ZoneInfo(settings.TIME_ZONE))
        self.assertEqual(dt.date(), sde.date())
        self.assertEqual(dt.hour, sde.hour)
