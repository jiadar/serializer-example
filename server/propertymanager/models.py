import uuid

import magic
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


class Inspection(models.Model):
    inspection_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=True
    )
    property = models.ForeignKey("property", on_delete=models.CASCADE)
    inspector = models.ForeignKey(User, on_delete=models.CASCADE)
    inspection_date = models.DateField(null=True, blank=True)
    findings = models.TextField()
    ORDER_BY = "inspection_id"


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
