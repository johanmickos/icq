"""
Custom database functions.
"""
from django.db.models import FloatField, Func


class CubeDistance(Func):
    """Uses the PostgreSQL distance function <-> to measure a float distance."""
    output_field = FloatField() # type: ignore
    function = ""
    arg_joiner = " <->"

class CubeEnlargeFunc(Func):
    """
    Increases the size of the cube by the specified radius r in at least n dimensions.

    Example usage:
        SiteColor.objects.filter(color_lab__contained_by=CubeEnlargeFunc(Cube((1,1,1)), 25, 0))
        SQL:
            SELECT "core_sitecolor"."id", "core_sitecolor"."color_lab", "core_sitecolor"."site_id"
            FROM "core_sitecolor"
            WHERE "core_sitecolor"."color_lab" <@ (cube_enlarge((1, 1, 1), 25, 0))
    """
    function = 'cube_enlarge'
    template = "%(function)s(%(expressions)s)"
