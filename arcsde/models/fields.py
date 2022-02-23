"""
    Arc SDE format fields cannot be manipulated with geo-django, which expects GEOS / OGC format data
    These fields are needed for spatial queries performed in the DB (using query annotations),
       but the fields should probably not be used in the app itself - they are just proprietary blobs of bits.
    Use the SdeManager to retrieve models with these fields - it will annotate the model with useful fields.
"""
from django.db.models.fields import TextField


class ArcSdePointField(TextField):

    description = "Arc SDE point - in Hex format"

    # def db_type(self, connection):
    #     return 'st_point'


class ArcSdeGeometryField(TextField):

    description = "Arc SDE geometry - in Hex format"

    # def db_type(self, connection):
    #     return 'st_geometry'


class ArcSdeLineField(TextField):

    description = "Arc SDE line - in Hex format"

    # def db_type(self, connection):
    #     return 'st_line'
