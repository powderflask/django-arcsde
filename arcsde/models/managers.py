"""
SDE feature model managers and querysets
@author: powderflask

Encapsulates the of details for performing queries on Arc SDE database.

Provides access to WKT text represenation and some simple spatial queries.
    Note: SDE stores shapes in proprietary Arc format, but django-gis only works with OGC format data
          Shapes may be converted to WKT (text) using sde, then back to a GEOS geometry using PostGIS:
"""
import datetime
from django.db import models
from arcsde import settings, util
from arcsde.models.functions import Latitude, Longitude, SdeAreaHa


class ArcSdeQuerySet(models.QuerySet):
    """
        Querysets for SDE feature models
    """
    SDE_EDITED_BY_ANNOTATION = 'arcsde_last_edited_user'

    ACTIVE_GDB_TO_DATE = datetime.datetime(9999, 12, 31, 23, 59, 59)

    def set_edited_by(self, username):
        """
        annotate records with username to be used to update SDE edit tracking field on save
        tightly coupled with ArcSdeRevisionFieldsMixin that uses this annotation to update  last_edited_user
        """
        return self.annotate(**{self.SDE_EDITED_BY_ANNOTATION: username})

    def sde_shape_as_text(self):
        """
          Return sde shape field geometry as a text (WKT) annotation.
          Assumes self.model.has_shape
       """
        return self.annotate(shape_text=models.Func(models.F('shape'), function='ST_ASTEXT'))

    #
    #  IF there is a need to support geo-django and django.contrib.gis models,
    #  this would retrieve geo-django spatial fields from the WKT above (will consider if use-case arises)
    #
    #def sde_text_as_geom(self):
    #    """
    #      Return text (WKT) geometry as a geos geometry annotation.
    #      Must be chained to sde_shape_as_text()
    #    """
    #    return self.annotate(shape_geos=Func(ExpressionWrapper(F('shape_text'), output_field=models.GeometryField()),
    #                                          function='ST_GeomFromText',
    #                                          template='%(function)s(%(expressions)s::character varying)'))

    def sde_area_from_shape(self, annotation_name='area'):
        """
          Return area of sde shape field geometry, in ha, as a numeric annotation.
          Assumes self.model.has_shape
       """
        annotation = {annotation_name: SdeAreaHa('shape')}
        return self.annotate(**annotation)

    def sde_latlong_from_shape(self):
        """
          Return sde point geometries in shape field as an (lat,long) text field annotation.
          ST_X(ST_Transform(shape, 4269)) as long,  ST_Y(ST_Transform(shape, 4269)) as lat
        """
        assert getattr(self.model, 'is_point', False),\
                "Attempt to annotate Lat/Long on a model without a Point shape field."

        return self.annotate(lat=Latitude('shape')) \
                   .annotate(long=Longitude('shape'))

    # Spatial queries are expensive, best done by a DB view or trigger that can be optimized in some way.
    # But it is possible to perform intersections and other spatial operations...
    #
    # def sde_intersects_geom(self, geom_text):
    #     """
    #         Add a where clause for the intersection of the given geometry (in WKT) and the shape field
    #         Assumes self.model.has_shape
    #     """
    #     srid = '3005'
    #     # use of extra is discouraged in the django docs:  https://docs.djangoproject.com/en/dev/ref/models/querysets/#extra
    #     return self.extra(where = ['ST_Intersects(ST_SetSrid(ST_GeomFromText(%s), %s), ST_SetSrid(ST_GeomFromText(st_astext("shape")::character varying), %s))'],
    #                       params= [geom_text, srid, srid])

    def sde_annotate_from_intersect(self, sde_model, field_name, where_constraint_field=None):
        """
            Add the given field_name from sde_model as an annotation, where this model intersects object from given sde_model
            Assumes self.model.has_shape and sde_model.has_shape
            Limit 1 for cases where query yields > 1 intersection
            where_constraint_field optinoally provides field name available on both models and constrains
                intersection to only objects that share same value in this field.  TODO: improve this API!
        """
        # noinspection PyProtectedMember
        extra_constraint = 'and lhs.{field} = {rhs}.{field}'.format(field=where_constraint_field,
                                                                    rhs=self.model._meta.db_table) \
            if where_constraint_field else ''

        # noinspection PyProtectedMember
        raw_query= """
          SELECT lhs.{field} FROM {lhs} AS lhs
            WHERE (ST_Intersects({rhs}.shape, lhs.shape) {extra_constraint})
            LIMIT 1
        """.format(
            field = field_name,
            rhs = self.model._meta.db_table,
            lhs = sde_model._meta.db_table,
            extra_constraint = extra_constraint
        )

        annotation = {field_name: models.expressions.RawSQL(raw_query, [])}
        return self.annotate(**annotation)

    def sde_defer_shape(self):
        assert(getattr(self.model, 'has_shape', False))
        return self.defer('shape')

    def sde_active(self):
        """
          Return only "active" (i.e. current) records from Arc SDE table with a "shape" field.
          These are identified by an "end of time" gdb_to_date value in the base table.
          If using EVW views, then archived records are pre-filtered, and all are "active"
          For models with a shape - don't fetch the shape itself - can't use it, don't want to tamper with it.
        """
        qs = self
        if not settings.SDE_USE_EVW:
            qs = qs.filter(gdb_to_date__gte=self.ACTIVE_GDB_TO_DATE)

        if getattr(self.model, 'has_shape', False):
            qs = qs.sde_defer_shape()

        return qs

    def with_attachments(self):
        """
            Prefetch attachments with the model instances
            Note: this is not much of a performance boost b/c the data loading overwhelms query times
                  and the default image attachment viewer does an async request for images any how.
                --> certainly NEVER do this unless you are 100% sure you will use ALL the attachments!
        """
        return self.prefetch_related('attachment_set')

    def annotate_attachment_count(self):
        """
        Add an attachment_count annotation to the model with the number of SDE attachments
        Warning: this method accesses model class variable - don't call it until models are loaded!
        """
        # return self.annotate(attachment_count=sde_attachment_count(self.model))
        annotation =  models.Count('attachment_set') if self.model.has_attachments() else models.Value(0)
        return self.annotate(attachment_count=annotation)

    @staticmethod
    def recent_period_start(period_in_hours):
        """ return a Datetime object representing the start time for a period that starts period_in_hours hours ago """
        return util.recent_period_start(period_in_hours)

    def recent_features(self, period_in_hours) :
        """ filter for features created in the past period_in_hours hours """
        period_start = self.recent_period_start(period_in_hours)
        return self.filter(created_date__gte=period_start).order_by('-created_date')


class ArcSdeManager(models.Manager.from_queryset(ArcSdeQuerySet)):
    """
        Arc SDE has some odd ideas about database relations...
          - "primary keys" that are not actually unique,
          - "archiving" that inserts a new "active" record to replace the existing record on update,
          - does not generally use the DB to maintain data integrity and fk relations -- all done in software.
        This manager attempts to abstract some of this weirdness away - should be used by ALL Arc SDE feature models.
    """
    def get_queryset(self):
        # all SDE report queries must start with sde_active!
        return super().get_queryset().sde_active()

    def recent_features(self, period_in_hours) :
        """ return a queryset of all features created in the past period_in_hours hours """
        return self.get_queryset().recent_features(period_in_hours)


class AnnotatedArcSdeManager(ArcSdeManager) :
    """ An ArcSdeManager that annotates and loads commonly needed related data onto report """
    def get_queryset(self):
        # SDE report queries often need SDE attachment_count
        return super().get_queryset().annotate_attachment_count()
