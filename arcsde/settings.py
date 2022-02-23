"""
SDE feature models
@author: powderflask

    Defaults for settings used by arcsde package.
"""
from django.conf import settings

TIME_ZONE = settings.TIME_ZONE
SDE_LOCAL_TIME_ZONE = getattr(settings, 'SDE_LOCAL_TIME_ZONE', 'UTC')

SDE_USE_EVW = getattr(settings, 'SDE_USE_EVW', True)