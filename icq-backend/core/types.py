"""
Domain-specific types.
"""
from ast import literal_eval as make_tuple

Cube = tuple

def make_cube(value)->Cube :
    """Constructs a cube from a tuple."""
    return make_tuple(value)
