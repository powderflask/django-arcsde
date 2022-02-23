"""
    SDE DB Functions.
"""
from django.db import models


class SdeAreaHa(models.Func):
    """
        A simple Expression that renders the area of an SDE shape field in HA
    """
    function = 'ST_Area'
    HA_PER_M2 = '0.0001'  # conversion factor to HA from m^2 -- ST_Area returns m^2

    def __init__(self, shape_field_name='shape') :
        super().__init__(
             models.F(shape_field_name),
             function=self.function,
             template="%(function)s(%(expressions)s) * " + self.HA_PER_M2,
        )


class BaseSdeShapeFunc(models.Func):
    """
         Base class for Query Expressions that work on an SDE shape field
    """
    function = None   # Sub-classes must set this to a valide SDE shape function
    def __init__(self, shape_field_name='shape', srid='4269') :
        super().__init__(
             models.F(shape_field_name),
             function=self.function,
             template='%(function)s(ST_Transform(%(expressions)s, %(srid)s))',
             srid=srid
        )

class Latitude(BaseSdeShapeFunc):
    """
        A simple Expression that renders the latitutde of an SDE shape field
    """
    function = 'ST_Y'

class Longitude(BaseSdeShapeFunc):
    """
        A simple Expression that renders the longitude of an SDE shape field
    """
    function = 'ST_X'
