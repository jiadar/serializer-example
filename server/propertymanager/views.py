import pdb

import magic
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import Error as DatabaseError
from marshmallow import fields
from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from rest_framework.response import Response

from .models import (Detail, Furniture, Inspection, InspectionItem, Property,
                     User, Vehicle)


class UserViewSet(magic.MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(User)

    class UserDefaultSchema(schema_cls):
        user_id = fields.UUID()
        email = fields.Email()
        phone = fields.String()
        dob = fields.Date()
        address = fields.String()
        city = fields.String()
        state = fields.String()
        zip = fields.Number()

    schemas = magic.SchemaContainer(UserDefaultSchema)


class FurnitureViewSet(magic.MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(Furniture)

    class FurnitureDefaultSchema(schema_cls):
        furniture_id = fields.UUID()
        description = fields.String()
        condition = fields.Number()
        inservice_date = fields.Date()
        expected_life = fields.Number()

    schemas = magic.SchemaContainer(FurnitureDefaultSchema)


class VehicleViewSet(magic.MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(Vehicle)

    class VehicleDefaultSchema(schema_cls):
        vehicle_id = fields.UUID()
        make = fields.String()
        model = fields.String()
        year = fields.Number()
        description = fields.String()
        last_maintenance = fields.Date()

    schemas = magic.SchemaContainer(VehicleDefaultSchema)


class DetailViewSet(magic.MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(Detail)

    class DetailDefaultSchema(schema_cls):
        detail_id = fields.UUID()
        description = fields.String()

    schemas = magic.SchemaContainer(DetailDefaultSchema)


class InspectionItemViewSet(magic.MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(InspectionItem)

    class InspectionItemDefaultSchema(schema_cls):
        inspection_item_id = fields.UUID()
        description = fields.String()
        details = fields.Nested(DetailViewSet.DetailDefaultSchema, many=True)

    schemas = magic.SchemaContainer(InspectionItemDefaultSchema)


class InspectionViewSet(magic.MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(Inspection)

    class InspectionDefaultSchema(schema_cls):
        inspection_id = fields.UUID()
        inspector = fields.UUID()
        inspection_date = fields.Date()
        findings = fields.String()

    class InspectionCreateSchema(schema_cls):
        inspection_id = fields.UUID()
        inspector_id = fields.UUID()
        inspection_date = fields.Date()
        findings = fields.String()
        inspection_items = fields.Nested(
            InspectionItemViewSet.InspectionItemDefaultSchema, many=True
        )

    schemas = magic.SchemaContainer(
        InspectionDefaultSchema,
        create=InspectionCreateSchema,
    )


class PropertyViewSet(magic.MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(Property)

    class PropertyDefaultSchema(schema_cls):
        property_id = fields.UUID()
        owner_id = fields.UUID()
        address = fields.String()
        city = fields.String()
        state = fields.String()
        zip = fields.Number()
        description = fields.String()
        rent = fields.Number()

    class PropertyCreateSchema(schema_cls):
        property_id = fields.UUID()
        owner_id = fields.UUID()
        address = fields.String()
        city = fields.String()
        state = fields.String()
        zip = fields.Number()
        description = fields.String()
        rent = fields.Number()
        inspections = fields.Nested(InspectionViewSet.InspectionCreateSchema, many=True)
        furniture_items = fields.Nested(
            FurnitureViewSet.FurnitureDefaultSchema, many=True
        )
        vehicles = fields.Nested(VehicleViewSet.VehicleDefaultSchema, many=True)

    schemas = magic.SchemaContainer(
        PropertyDefaultSchema,
        create=PropertyCreateSchema,
    )
