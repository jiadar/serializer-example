import uuid

from django.db import models
from marshmallow import Schema, fields


# Create your models here.
class User(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    email = models.EmailField(max_length=255, unique=True)
    phone = models.CharField(max_length=17, blank=True)
    dob = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=128, blank=True)
    city = models.CharField(max_length=64, blank=True)
    state = models.CharField(max_length=64, blank=True)
    zip = models.CharField(max_length=12, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["email"]
    ORDER_BY = "email"

    class schema:
        class default(Schema):
            user_id = fields.UUID()
            email = fields.Email()
            phone = fields.String()
            dob = fields.Date()
            address = fields.String()
            city = fields.String()
            state = fields.String()
            zip = fields.Number()


class Inspection(models.Model):
    inspection_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=True
    )
    property = models.ForeignKey("property", on_delete=models.CASCADE)
    inspector = models.ForeignKey(User, on_delete=models.CASCADE)
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


class Property(models.Model):
    property_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=128, blank=True)
    city = models.CharField(max_length=64, blank=True)
    state = models.CharField(max_length=64, blank=True)
    zip = models.CharField(max_length=12, blank=True)
    description = models.TextField(blank=True)
    rent = models.FloatField(blank=True)

    ORDER_BY = "property_id"

    class schema:
        dependents = [
            ("inspection", "Inspection", "create"),
        ]

        def has_dependents(self):
            return len(self.dependents) > 0

        default = Schema.from_dict(
            {
                "property_id": fields.UUID(),
                "owner_id": fields.UUID(),
                "address": fields.String(),
                "city": fields.String(),
                "state": fields.String(),
                "zip": fields.Number(),
                "description": fields.String(),
                "rent": fields.Number(),
            }
        )

        create = Schema.from_dict(
            {
                "property": fields.Nested(default),
                "inspection": fields.Nested(Inspection.schema.create),
            }
        )

        class list(Schema):
            property_id = fields.UUID()
            owner = fields.Nested(User.schema.default)
            address = fields.String()
            city = fields.String()
            state = fields.String()
            zip = fields.Number()
            description = fields.String()
            rent = fields.Number()
