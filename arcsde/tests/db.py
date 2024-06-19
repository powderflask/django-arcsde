"""
    To run tests with dynamic SDE at attachment models (e.g., created by ArcSdeAttachmentsDescriptor)
    we need to populate the test DB with the SDE attach tables to back those dynamic models.
    This can be done AFTER the test DB is create, but BEFORE and tests are actually run:
      the pre-migrate or post-migrate signals provide a reasonable hook.
"""
from django.apps import apps
from django.db import connection
from arcsde.attachments import descriptors
from arcsde.util import all_members

CREATE = (
    'BEGIN',
    '''
     CREATE TABLE "{attach_table}" ("globalid" varchar(38) NOT NULL UNIQUE,
                                    "attachmentid" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                                    "content_type" varchar(150) NOT NULL,
                                    "att_name" varchar(250) NOT NULL,
                                    "data_size" integer NOT NULL,
                                    "data" BLOB NULL,
                                    "rel_globalid" varchar(38) NOT NULL)
    ''',
    'CREATE INDEX "{attach_table}_rel_globalid_{globalid}" ON "{attach_table}" ("rel_globalid")',
    'COMMIT'
)

def create_sde_attach_tables(descriptor='sde_attachments', verbosity=0):
    """ Create SDE __attach tables for any model classes with an ArcSdeAttachmentsDescriptor descriptor """
    from .models import mock_globalid

    tables = {None, }  # don't double create attach table, e.g., where both table-backed and view-backed model exist
    with connection.cursor() as cursor:
        if verbosity > 0:
            print('  Creating SDE attach tables...')
        for model in apps.get_models():
            sde_attachments = all_members(model).get(descriptor, None)
            table = sde_attachments.get_attachments_db_table_name(model) \
                if sde_attachments and isinstance(sde_attachments, descriptors.ArcSdeAttachmentsDescriptor) else None
            if table not in tables:
                tables.add(table)
                if verbosity>0:
                    print('    Creating table {attach_table} for model {model}'.format(
                        attach_table=table, model=model.__name__)
                    )
                for sql in (statement.format(attach_table=table, globalid=mock_globalid()) for statement in CREATE):
                    cursor.execute(sql)


def create_sde_attach_tables_receiver(sender, descriptor='sde_attachments', **kwargs):
    """ Signal receiver for create_sde_attach_tables """
    create_sde_attach_tables(descriptor, kwargs.get('verbosity', 0))

def mock_sde_functions(conn):
    """ Add suite of mock functions to SQLite DB so SDE stored proc. calls don't crash -- dummy results!! """
    # Mock SDE functions defined in arcsde.models.functions:
    def ST_Transform(expr, srid):
        return 42.0
    def ST_X(shape):
        return 123
    def ST_Y(shape):
        return 987
    def ST_Area(shape):
        return 31400
    def ST_Intersects(shape1, shape2):
        return False
    functions = ((ST_Transform, 2), (ST_X, 1), (ST_Y, 1), (ST_Area, 1), (ST_Intersects, 2) )

    for fn, n_arg in functions:
        conn.connection.create_function(fn.__name__, n_arg, fn)


def create_tables_for_unmanaged_test_models(conn):
    from .models import SdeFeatureModel_ddl
    with conn.cursor() as cursor:
        cursor.execute(SdeFeatureModel_ddl)
