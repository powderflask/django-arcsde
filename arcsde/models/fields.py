"""
    Arc SDE format fields cannot be manipulated with geo-django, which expects GEOS / OGC format data
    These fields are needed for spatial queries performed in the DB (using query annotations),
       but the fields should probably not be used in the app itself - they are just proprietary blobs of bits.
    Use the SdeManager to retrieve models with these fields - it will annotate the model with useful fields.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

from arcsde import tz


class ArcSdePointField(models.TextField):

    description = "Arc SDE point - in Hex format"

    # def db_type(self, connection):
    #     return 'st_point'


class ArcSdeGeometryField(models.TextField):

    description = "Arc SDE geometry - in Hex format"

    # def db_type(self, connection):
    #     return 'st_geometry'


class ArcSdeLineField(models.TextField):

    description = "Arc SDE line - in Hex format"

    # def db_type(self, connection):
    #     return 'st_line'


class ArcSdeDateTimeField(models.DateTimeField):
    """ A DateTimeField that yields a localized datetime based on TIME_ZONE setting

    Arc SDE stores all datetime data in UTC without timezone :-(
    This field provides basic timezone-aware datetime object in TIME_ZONE converted to/from SDE_DB_TIME_ZONE (UTC)
    """

    description = "Arc SDE localized DateTime field (see settings.SDE_DB_TIME_ZONE)"

    def from_db_value(self, value, expression, connection):
        """ Take a naive UTC datetime from DB and convert to aware local TZ. """
        if value and not settings.USE_TZ and timezone.is_naive(value):
            # This should always be true for SDE-backed DB, which store naive datetime, so should not USE_TZ
            # Localize the datetime from UTC to settings.TIME_ZONE
            value = tz.localize(value)
        return value

    def get_prep_value(self, value):
        """ Convert value to UTC datetime, ready to store in DB. """
        value = super().get_prep_value(value)
        if value and not settings.USE_TZ:
            # USE_TZ should always be False for SDE-backed DB
            # Convert datatime to UTC, if it is naive, assume it is in local TIME_ZONE
            value = tz.delocalize(value).replace(tzinfo=None)
        return value
