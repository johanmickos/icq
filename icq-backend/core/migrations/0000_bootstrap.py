
from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):
    """Bootstrap migrations to be run before the auto-generated ones."""

    run_before = [
        ('core', '0001_initial'),
    ]

    operations = [
        CreateExtension('cube'), # Enable 'cube' support for LAB color queries and indexing
    ]
