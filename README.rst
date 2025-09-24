Django ArcSDE
=============

Abstractions and base classes for creating django models from Arc SDE feature tables.

 * Version: 1.4.6
 * Author: powderflask
 * License: MIT
 * URI: https://github.com/powderflask/django-arcsde
 * Documentation: https://django-arcsde.readthedocs.io.

Overview
--------

ArcSDE Spatial Database Engine employs enough standard conventions that one can build a django
app to interact with its DB.  Functionality is somewhat limited,
generally relying on unmanaged models created and maintained using Arc toolset,
but for reporting, analysis, data mining, etc., this works well.

Features
--------

* base classes for working with SDE feature models
* queryset can use EVW views (recommended) or base SDE tables (filtered by gbd_to_date)
* dynamic SDE attachment models by simply adding descriptor to feature model

Quick Start
-----------

* ``pip install https://github.com/powderflask/django-arcsde.git``
* ``python3 setup.py test``   (to run app test suite)
* Add ``arcsde`` to ``INSTALLED_APPS`` ::

    INSTALLED_APPS = [
        ...
        'arcsde',
    ]

Testing
-------

Unit tests must be run with ``DJANGO_SETTINGS=arcsde.tests.settings``
arcsde.tests.models create a dummy SDE-like model with attachment table for testing.

**migrations for test models**

* tests.models don't have migrations - test DB is defined directly from models
* depends on MIGRATION_MODULES setting in tests.settings! (https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules)

