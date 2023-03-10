import uuid

from django.db import models
from marshmallow import Schema, fields
from users.models import User


# Create your models here.
class Inspection(models.Model):
    inspection_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=True
    )
    property = models.ForeignKey("properties.property", on_delete=models.CASCADE)
    inspector = models.ForeignKey("users.User", on_delete=models.CASCADE)
    inspection_date = models.DateField(null=True, blank=True)
    findings = models.TextField()
    ORDER_BY = "inspection_id"

    class schema:
        class create(Schema):
            inspection_id = fields.UUID()
            inspector = fields.UUID()
            inspection_date = fields.Date()
            findings = fields.String()

        class list(Schema):
            inspection_id = fields.UUID()
            inspector = fields.Nested(User.schema.default)
            inspection_date = fields.Date()
            findings = fields.String()

        class default(Schema):
            inspection_id = fields.UUID()
            inspector = fields.UUID()
            inspection_date = fields.Date()
            findings = fields.String()
