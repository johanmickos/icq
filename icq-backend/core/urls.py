from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("colors", views.colors, name="colors"),
    path("similar/<str:hexcolor>", views.similar, name="similar"),
    path("scrape", views.scrape, name="scrape"),
    path("latest", views.latest, name="latest"),
    path("job/<int:job_id>", views.job, name="latest"),
    path("site/<int:site_id>", views.site, name="site"),
]
