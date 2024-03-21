from django.contrib import admin

from . import models

admin.site.register(models.Site)
admin.site.register(models.SitePageType)
admin.site.register(models.DataSource)
admin.site.register(models.ColorDataResult)
admin.site.register(models.SiteColor)
admin.site.register(models.SiteCategory)
