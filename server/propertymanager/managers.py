from django.db import models

"""Managers

While models should have ORM logic that operates on a row level, Managers should have the
ORM logic that operates on the table level. If the logic applies to more than one model
instance (queryset) then put it here.
"""


class UserManager(models.Manager):
    pass


class InspectionManager(models.Manager):
    pass


class InspectionItemManager(models.Manager):
    pass


class DetailManager(models.Manager):
    pass


class FurnitureManager(models.Manager):
    pass


class VehicleManager(models.Manager):
    pass


class PropertyManager(models.Manager):
    pass
