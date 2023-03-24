import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import autoreload


def clean_database():
    os.system(
        "PGPASSWORD=example psql -U example example -h 127.0.0.1 < /Users/javin/work/serializer-example/server/clean-database.sql"
    )

    # should get this to run even if there are errors, wrap it somehow
    #


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Cleaning database with autoreload...")
        autoreload.run_with_reloader(clean_database)
