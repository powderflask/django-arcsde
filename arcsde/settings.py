"""
SDE feature models
@author: powderflask

    Defaults for settings used by arcsde package.
"""
from django.conf import settings

TIME_ZONE = settings.TIME_ZONE
SDE_DB_TIME_ZONE = getattr(settings, 'SDE_DB_TIME_ZONE', 'UTC')  # AFAIK UTC is non-negotiable - documentation only.

SDE_USE_EVW = getattr(settings, 'SDE_USE_EVW', True)

# This feature maintains SDE feature edit tracking fields on models that mixin ArcSdeRevisionFieldsMixin
# It does require that SDE feature querysets include .set_edited_by(username) to pass thru the request user's username
# Be certain before disabling this feature - better to consciously not use the ArcSdeRevisionFieldsMixin.
SDE_EDIT_TRACKING = getattr(settings, 'SDE_EDIT_TRACKING', True)

# Default value to use in production environment where client code fails to .set_edited_by(username) on saved instance
# Need to write something to this field - a error is logged if this value is ever used.
SDE_EDIT_TRACKING_DEFAULT_USERNAME = getattr(settings, 'SDE_EDIT_TRACKING_DEFAULT_USERNAME', 'django-sde-webapp')

# Default value enables concurrency detection and locks on SDE forms.
# Set to False to disable concurrency detection.
SDE_CONCURRENCY_LOCK = getattr(settings, 'SDE_CONCURRENCY_LOCK', True)
