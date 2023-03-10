import uuid

from django.db import models
from inspections.models import Inspection
from marshmallow import Schema, fields
from users.models import User


# Create your models here.
class Property(models.Model):
    property_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    owner = models.ForeignKey("users.User", on_delete=models.CASCADE)
    address = models.CharField(max_length=128, blank=True)
    city = models.CharField(max_length=64, blank=True)
    state = models.CharField(max_length=64, blank=True)
    zip = models.CharField(max_length=12, blank=True)
    description = models.TextField(blank=True)
    rent = models.FloatField(blank=True)

    ORDER_BY = "property_id"

    class schema:
        class default(Schema):
            property_id = fields.UUID()
            owner_id = fields.UUID()
            address = fields.String()
            city = fields.String()
            state = fields.String()
            zip = fields.Number()
            description = fields.String()
            rent = fields.Number()

        class create(Schema):
            property_id = fields.UUID()
            owner_id = fields.UUID()
            address = fields.String()
            city = fields.String()
            state = fields.String()
            zip = fields.Number()
            description = fields.String()
            rent = fields.Number()
            inspection = fields.Nested(Inspection.schema.default)

        class list(Schema):
            property_id = fields.UUID()
            owner = fields.Nested(User.schema.default)
            address = fields.String()
            city = fields.String()
            state = fields.String()
            zip = fields.Number()
            description = fields.String()
            rent = fields.Number()
