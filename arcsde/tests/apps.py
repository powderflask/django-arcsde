from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.dispatch import receiver


class ArcSdeTestsConfig(AppConfig):
    name = 'arcsde.tests'
    label = 'arcsde_tests'
    verbose_name = "Arc SDE Testing app"

    def ready(self):
        """ Create any missing SDE Attach tables for Dynamic attachments models """
        from django.db.models.signals import pre_migrate, post_migrate
        from arcsde.tests.db import create_sde_attach_tables_receiver
        post_migrate.connect(create_sde_attach_tables_receiver, sender=self)


@receiver(connection_created)
def extend_sqlite(connection=None, **kwargs):
    """ Mock up SDE functions on the sqlite test DB """
    from . import db
    if connection.vendor == 'sqlite':  # only applies to SQLite DB, used for running quick tests
        db.mock_sde_functions(connection)
