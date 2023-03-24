import uuid

from django.db import models


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


class Inspection(models.Model):
    inspection_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=True
    )
    inspector = models.ForeignKey(User, on_delete=models.CASCADE)
    inspection_date = models.DateField(null=True, blank=True)
    findings = models.TextField()
    property = models.ForeignKey("Property", on_delete=models.CASCADE)


class InspectionItem(models.Model):
    inspection_item_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=True
    )
    inspection = models.ForeignKey("Inspection", on_delete=models.CASCADE)
    description = models.TextField()


class Detail(models.Model):
    detail_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    inspection_item = models.ForeignKey("InspectionItem", on_delete=models.CASCADE)
    description = models.TextField()


class Furniture(models.Model):
    furniture_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    description = models.TextField(null=True, blank=True)
    condition = models.IntegerField(null=True, blank=True)
    inservice_date = models.DateField(null=True, blank=True)
    expected_life = models.IntegerField(null=True, blank=True)
    property = models.ForeignKey("Property", on_delete=models.CASCADE)


class Vehicle(models.Model):
    vehicle_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    make = models.CharField(max_length=64, null=True, blank=True)
    model = models.CharField(max_length=64, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    properties = models.ManyToManyField("Property")


class Property(models.Model):
    property_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=128, blank=True)
    city = models.CharField(max_length=64, blank=True)
    state = models.CharField(max_length=64, blank=True)
    zip = models.CharField(max_length=12, blank=True)
    description = models.TextField(blank=True)
    rent = models.FloatField(blank=True)
    vehicles = models.ManyToManyField(Vehicle)
