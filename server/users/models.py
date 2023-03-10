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
