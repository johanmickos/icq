from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        post_migrate.connect(create_required_objects, sender=self)


def create_required_objects(sender, **kwargs):
    # site = Site.objects.create()

    # ColorData.objects.create(
    #     site=site,
    #     lab_l=0.0,
    #     lab_a=0.0,
    #     lab_b=0.0,
    # )
    return
