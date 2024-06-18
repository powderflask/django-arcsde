"""
    Utility functions used by arcsde package.
"""
from django.utils import timezone

from datetime import timedelta


def recent_period_start(period_in_hours):
    """ return a Datetime object representing the start time for a period that starts period_in_hours hours ago """
    return timezone.now() - timedelta(hours=period_in_hours)


def all_members(aClass):
    """ Return dict of all Class members without actually accessing them (e.g., cached_property or descriptors) """
    mro = reversed(list(aClass.__mro__))
    members = {}
    for someClass in mro:
        members.update(vars(someClass))
    return members
