from django.db import models

"""Managers
Managers should have ORM logic that operates on table level.

The manager is the thing that you get when you call Model.objects. It should deal with querysets.

If you need to operate on the row level (on a single model instance), that should probably go
in the model.If the logic applies to more than one model instance (queryset) then put it here.
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
