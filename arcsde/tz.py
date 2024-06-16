""" SDE stores all datetime fields in UTC - a few forms need to work on these in local timezone """
from zoneinfo import ZoneInfo
from django.utils import timezone
from arcsde import settings

LOCAL_TIME_ZONE = ZoneInfo(settings.TIME_ZONE)
SDE_DB_TIME_ZONE = ZoneInfo(settings.SDE_DB_TIME_ZONE)


def localize(datetime):
    """
    Localize a datetime object, possibly naive in SDE native time zone (UTC),
    to LOCAL_TIME_ZONE defined in settings
    """
    if datetime is None:
        return None
    try:
        # Force SDE TZ on naive datetime from DB.
        dt = timezone.make_aware(datetime, timezone=SDE_DB_TIME_ZONE) \
            if timezone.is_naive(datetime) else datetime

        # Transform SDE TZ datetime to local TZ
        return dt.astimezone(LOCAL_TIME_ZONE)
    except OverflowError:
        return None


def delocalize(datetime):
    """
    De-localize a datetime object, possibly naive in LOCAL_TIME_ZONE, to SDE_DB_TIME_ZONE
    """
    if datetime is None:
        return None
    try:
        # Force Local TZ on naive datetime (default interpretation anyhow, but for consistency).
        dt = timezone.make_aware(datetime, timezone=LOCAL_TIME_ZONE) \
             if timezone.is_naive(datetime) else datetime

        # Transform Local TZ datetime to SDE TZ
        return dt.astimezone(SDE_DB_TIME_ZONE)
    except OverflowError:
        return None
