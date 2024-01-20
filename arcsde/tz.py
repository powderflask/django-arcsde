""" SDE stores all datetime fields in UTC - a few forms need to work on these in local timezone """
from zoneinfo import ZoneInfo
from arcsde import settings

LOCAL_TIME_ZONE = ZoneInfo(settings.SDE_LOCAL_TIME_ZONE)
SDE_BASE_TIMEZONE = ZoneInfo(settings.TIME_ZONE)

def localize(datetime):
    """
    Localize a datetime object, possibly naive in SDE native time zone (UTC),
    to LOCAL_TIME_ZONE defined in settings
    """
    if datetime is None:
        return None
    try:
        # Force dt to SDE TZ.  For naive dt objects, this will just set tzinfo without any tz transform.
        dt = datetime.astimezone(SDE_BASE_TIMEZONE)
        # Transform dt to local time zone
        return dt.astimezone(LOCAL_TIME_ZONE)
    except OverflowError:
        return None

def delocalize(datetime):
    """
    De-localize a datetime object, possibly naive in LOCAL_TIME_ZONE, to SDE_BASE_TIMEZONE
    """
    if datetime is None:
        return None
    try:
        dt = datetime.astimezone(LOCAL_TIME_ZONE)
        return dt.astimezone(SDE_BASE_TIMEZONE)
    except OverflowError:
        return None
