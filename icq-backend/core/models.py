"""
Database models for ICQ.
"""
from dataclasses import dataclass
from typing import Tuple

import numpy as np
from core.colors import lab2hex, lab2rgb
from django.contrib.gis.db import models
from django.contrib.postgres.indexes import GistIndex

from .fields import CubeField


class Site(models.Model):
    """Root object for a website on the Internet"""

    url = models.URLField(unique=True)
    domain = models.URLField()  # Shared across many Site instances
    name = models.CharField(max_length=100)
    categories = models.ManyToManyField('SiteCategory')
    page_type = models.ForeignKey('SitePageType', on_delete=models.PROTECT)

    def __str__(self):
        return str(self.url)


class SiteCategory(models.Model):
    """Describes how a website can be categorized (e.g. "internet search", "personal blog")"""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return str(self.name)


class SitePageType(models.Model):
    """Describes a web page's function (e.g. "homepage", "blog entry", "Instagram profile")"""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return str(self.name)


class DataSource(models.Model):
    """Describes a blob of data used to extract website features."""

    class DataSourceType(models.TextChoices):
        """Supported data sources."""

        SCREENSHOT = "screenshot"
        HTML = "html"
        CSS = "css"
        FAVICON = "favicon"
        IMAGE = "image"

    created_at = models.DateTimeField(auto_now_add=True)
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    object_type = models.CharField(
        max_length=20, choices=DataSourceType.choices)
    object_url = models.URLField()
    object_checksum = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f'{self.site.domain} ({self.object_type}) - {self.object_checksum}'


class ScrapeJob(models.Model):
    """Specific instance of a website scraping job."""

    state = models.CharField(max_length=100)  # TODO: Enum
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class ScrapeJobSummary(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    job = models.OneToOneField(
        ScrapeJob,
        null=True,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # TODO: Summarize dominant colors, font color, etc. with denorm
    dominant_colors_visual = models.JSONField()
    dominant_colors_web = models.JSONField()
    dominant_colors_brand = models.JSONField()


class ScrapeJobConfiguration(models.Model):
    # TODO: Determine exactly what we need
    site = models.OneToOneField(Site, on_delete=models.CASCADE)
    scrape_interval_seconds = models.IntegerField()
    scrape_max_retries = models.IntegerField()
    scrape_retry_interval_seconds = models.IntegerField()


class DefaultColorResultTypeManager(models.Manager):
    """Model manager for supplying default result types."""

    VISUAL_SCREENSHOT = "visual-screenshot"
    VISUAL_FAVICON = "visual-favicon"

    def visual_screenshot(self):
        """Returns the default 'visual screenshot' result type."""
        obj, _ = self.get_or_create(name=self.VISUAL_SCREENSHOT)
        return obj

    def visual_favicon(self):
        """Returns the default 'visual favicon' result type."""
        obj, _ = self.get_or_create(name=self.VISUAL_FAVICON)
        return obj


@dataclass
class ColorGroup:
    name: str
    hex: str
    rgb: Tuple[int, int, int]
    lab: Tuple[float, float, float]

    def __init__(self, name: str, rgb: Tuple[int, int, int]):
        self.name = name
        self.color_rgb = rgb
        self.


COLOR_GROUPS = [
    ColorGroup("black", "#000000", (0, 0, 0)),
    ColorGroup("silver", "#C0C0C0", (192, 192, 192)),
    ColorGroup("gray", "#808080", (128, 128, 128)),
    ColorGroup("white", "#FFFFFF", (255, 255, 255)),
    ColorGroup("maroon", "#800000", (128, 0, 0)),
    ColorGroup("red", "#FF0000", (255, 0, 0)),
    ColorGroup("purple", "#800080", (128, 0, 128)),
    ColorGroup("fuchsia", "#FF00FF", (255, 0, 255)),
    ColorGroup("green", "#008000", (0, 128, 0)),
    ColorGroup("lime", "#00FF00", (0, 255, 0)),
    ColorGroup("olive", "#808000", (128, 128, 0)),
    ColorGroup("yellow", "#FFFF00", (255, 255, 0)),
    ColorGroup("navy", "#000080", (0, 0, 128)),
    ColorGroup("blue", "#0000FF", (0, 0, 255)),
    ColorGroup("teal", "#008080", (0, 128, 128)),
    ColorGroup("aqua", "#00FFFF", (0, 255, 255)),
]


class ColorLABMixin(models.Model):
    """
    Adds a 'color_lab' column with the PostgreSQL 'cube' type.
    """

    class Meta:
        abstract = True

    # class ColorGroup(models.TextChoices):
    #     """Predefined color groups for visual queries"""

    #     BLACK = ("#000000", (0, 0, 0), "black")
    #     SILVER = ("#C0C0C0", (192, 192, 192), "silver")
    #     GRAY = ("#808080", (128, 128, 128), "gray")
    #     WHITE = ("#FFFFFF", (255, 255, 255), "white")
    #     MAROON = ("#800000", (128, 0, 0), "maroon")
    #     RED = ("#FF0000", (255, 0, 0), "red")
    #     PURPLE = ("#800080", (128, 0, 128), "purple")
    #     FUCHSIA = ("#FF00FF", (255, 0, 255), "fuchsia")
    #     GREEN = ("#008000", (0, 128, 0), "green")
    #     LIME = ("#00FF00", (0, 255, 0), "lime")
    #     OLIVE = ("#808000", (128, 128, 0), "olive")
    #     YELLOW = ("#FFFF00", (255, 255, 0), "yellow")
    #     NAVY = ("#000080", (0, 0, 128), "navy")
    #     BLUE = ("#0000FF", (0, 0, 255), "blue")
    #     TEAL = ("#008080", (0, 128, 128), "teal")
    #     AQUA = ("#00FFFF", (0, 255, 255), "aqua")

    #     def __new__(cls, hex, rgb):
    #         obj = str.__new__(cls, hex)
    #         obj._value = hex
    #         obj.rgb = rgb
    #         return obj

    color_lab = CubeField()

    @property
    def color_group(self):
        def distance(v):
            a = v.color_lab
            ref = np.array([100, 0, 0])
            return np.linalg.norm(a-ref)
        return sorted(COLOR_GROUPS, key=distance)

    def __str__(self) -> str:
        return f'LAB({self.color_lab[:]})'

    def rgb(self):
        """Return the core.types.RGB representation of this color."""
        return lab2rgb(np.array(self.color_lab))

    def hex(self):
        """Return the core.types.HEX representation of this color."""
        return lab2hex(np.array(self.color_lab))


class SiteColor(ColorLABMixin):
    """Mapping of all colors ever found for every site."""
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'SiteColor{self.color_lab}'

    class Meta:
        unique_together = ('site', 'color_lab')
        indexes = [
            GistIndex(fields=['color_lab'])
        ]


class ColorDataResultType(models.Model):
    """Database-backed types for color data results (e.g. 'visual-screenshot', 'css-font')"""

    types = DefaultColorResultTypeManager()

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return str(self.name)


class ColorDataResult(ColorLABMixin):
    """Single color data point extracted from a website as part of a scrape job."""

    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    job = models.ForeignKey(ScrapeJob, on_delete=models.CASCADE)

    collected_at = models.DateTimeField(auto_now_add=True)
    result_type = models.ForeignKey(
        ColorDataResultType, on_delete=models.CASCADE)
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE)

    def __str__(self):
        return f'ColorDataResult({self.color_lab}, site_id={self.site})'
