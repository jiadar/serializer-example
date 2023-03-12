import pdb

import magic
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import Error as DatabaseError
from marshmallow import Schema, fields
from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from rest_framework.response import Response

from .models import Furniture, Inspection, Property, User, Vehicle


class UserViewSet(magic.MarshmallowViewSet):
    model = User

    class DefaultSchema(Schema):
        user_id = fields.UUID()
        email = fields.Email()
        phone = fields.String()
        dob = fields.Date()
        address = fields.String()
        city = fields.String()
        state = fields.String()
        zip = fields.Number()

    schemas = magic.SchemaContainer(DefaultSchema(), list=DefaultSchema(many=True))


class FurnitureViewSet(magic.MarshmallowViewSet):
    model = Furniture

    class DefaultSchema(Schema):
        furniture_id = fields.UUID()
        description = fields.String()
        condition = fields.Number()
        inservice_date = fields.Date()
        expected_life = fields.Number()

    schemas = magic.SchemaContainer(DefaultSchema(), list=DefaultSchema(many=True))


class VehicleViewSet(magic.MarshmallowViewSet):
    model = Vehicle

    class DefaultSchema(Schema):
        vehicle_id = fields.UUID()
        make = fields.String()
        model = fields.String()
        year = fields.Number()
        description = fields.String()
        last_maintenance = fields.Date()

    schemas = magic.SchemaContainer(DefaultSchema(), list=DefaultSchema(many=True))


class InspectionViewSet(magic.MarshmallowViewSet):
    model = Inspection

    class DefaultSchema(Schema):
        inspection_id = fields.UUID()
        inspector = fields.UUID()
        inspection_date = fields.Date()
        findings = fields.String()

    class CreateSchema(Schema):
        inspection_id = fields.UUID()
        inspector_id = fields.UUID()
        inspection_date = fields.Date()
        findings = fields.String()

    schemas = magic.SchemaContainer(
        DefaultSchema(), create=CreateSchema(), list=DefaultSchema(many=True)
    )


class PropertyViewSet(magic.MarshmallowViewSet):
    model = Property

    class DefaultSchema(Schema):
        property_id = fields.UUID()
        owner_id = fields.UUID()
        address = fields.String()
        city = fields.String()
        state = fields.String()
        zip = fields.Number()
        description = fields.String()
        rent = fields.Number()

    class CreateSchema(Schema):
        property_id = fields.UUID()
        owner_id = fields.UUID()
        address = fields.String()
        city = fields.String()
        state = fields.String()
        zip = fields.Number()
        description = fields.String()
        rent = fields.Number()
        inspection = fields.Nested(InspectionViewSet.schemas.create)
        furniture = fields.Nested(FurnitureViewSet.schemas.list)
        vehicles = fields.Nested(VehicleViewSet.schemas.list)

    relations = [
        magic.Relation("inspection", model=Inspection, related_field="property"),
        magic.Relation("furniture", model=Furniture, related_field="property"),
        magic.Relation("vehicles", model=Vehicle, related_field="vehicles", many=True),
    ]

    schemas = magic.SchemaContainer(
        DefaultSchema(),
        create=CreateSchema(),
        list=DefaultSchema(many=True),
        relations=relations,
    )
