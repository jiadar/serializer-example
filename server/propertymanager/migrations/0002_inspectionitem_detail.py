# Generated by Django 4.1.7 on 2023-03-24 18:15

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("propertymanager", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="InspectionItem",
            fields=[
                (
                    "inspection_item_id",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                ("description", models.TextField()),
                (
                    "inspection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="propertymanager.inspection",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Detail",
            fields=[
                (
                    "detail_id",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                ("description", models.TextField()),
                (
                    "inspection_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="propertymanager.inspectionitem",
                    ),
                ),
            ],
        ),
    ]
