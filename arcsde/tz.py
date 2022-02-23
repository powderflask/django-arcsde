""" SDE stores all datetime fields in UTC - a few forms need to work on these in local timezone """
import pytz
from arcsde import settings

LOCAL_TIME_ZONE = pytz.timezone(settings.SDE_LOCAL_TIME_ZONE)
SDE_BASE_TIMEZONE = pytz.timezone(settings.TIME_ZONE)

def localize(datetime):
    if datetime is None:
        return None
    try:
        dt = SDE_BASE_TIMEZONE.localize(datetime) if datetime.tzinfo is None else datetime
        return dt.astimezone(LOCAL_TIME_ZONE)
    except OverflowError:
        return None

def delocalize(datetime):
    if datetime is None:
        return None
    try:
        dt = LOCAL_TIME_ZONE.localize(datetime) if datetime.tzinfo is None else datetime
        return dt.astimezone(SDE_BASE_TIMEZONE)
    except OverflowError:
        return None
