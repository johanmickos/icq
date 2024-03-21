"""
Custom Django fields.
"""
from typing import Optional

from core.types import Cube, make_cube
from django.contrib.postgres.lookups import ContainedBy
from django.db import models


class CubeField(models.Field):
    """
    Custom field for the PostgreSQL data type 'cube'.
    Serializes to the generic form "'(%s, %s, ... %s)'::cube"
    """
    def db_type(self, connection):
        if connection.vendor != 'postgresql':
            raise RuntimeError(f'Vendor must be "postgresql", got "{connection.vendor}"')
        return 'cube'

    def from_db_value(self, value, _expression, _connection):
        if value is None:
            return
        return make_cube(value)

    def to_python(self, value)->Optional[Cube]:
        if isinstance(value, Cube):
            return value
        if value is None:
            return value
        return make_cube(value)

 # Add ${CubeField}__contained_by support
 # for queries like nearest neighbor(s).
CubeField.register_lookup(ContainedBy)
