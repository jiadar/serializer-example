import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import autoreload


def clean_database():
    os.system(
        "sqlite3 /Users/javin/work/serializer-example/server/db.sqlite3 < /Users/javin/work/serializer-example/server/clean-database.sh"
    )


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Cleaning database with autoreload...")
        autoreload.run_with_reloader(clean_database)
