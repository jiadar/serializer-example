import pdb

import magic
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import Error as DatabaseError
from marshmallow import Schema, fields
from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from rest_framework.response import Response

from .models import (Furniture, Inspection, InspectionItem, Property, User,
                     Vehicle)


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

    schemas = magic.SchemaContainer("user", DefaultSchema)


class FurnitureViewSet(magic.MarshmallowViewSet):
    model = Furniture

    class DefaultSchema(Schema):
        furniture_id = fields.UUID()
        description = fields.String()
        condition = fields.Number()
        inservice_date = fields.Date()
        expected_life = fields.Number()

    schemas = magic.SchemaContainer("furniture", DefaultSchema)


class VehicleViewSet(magic.MarshmallowViewSet):
    model = Vehicle

    class DefaultSchema(Schema):
        vehicle_id = fields.UUID()
        make = fields.String()
        model = fields.String()
        year = fields.Number()
        description = fields.String()
        last_maintenance = fields.Date()

    schemas = magic.SchemaContainer("vehicle", DefaultSchema)


class InspectionItemViewSet(magic.MarshmallowViewSet):
    model = InspectionItem

    class DefaultSchema(Schema):
        inspection_item_id = fields.UUID()
        description = fields.String()

    schemas = magic.SchemaContainer("inspection_item", DefaultSchema)


class InspectionViewSet(magic.MarshmallowViewSet):
    model = Inspection
    nested_fields = ["inspection_items"]

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
        inspection_items = fields.Dict(
            keys=fields.Str(),
            values=fields.Dict(
                keys=fields.Constant("inspection_item"),
                values=fields.Nested(InspectionItemViewSet.DefaultSchema),
            ),
        )

    relations = [
        magic.Relation(
            "inspection_items", model=InspectionItem, related_field="inspection"
        ),
    ]

    schemas = magic.SchemaContainer(
        "inspection",
        DefaultSchema,
        create=CreateSchema,
        relations=relations,
    )


class PropertyViewSet(magic.MarshmallowViewSet):
    model = Property
    root_key = "property"
    nested_fields = ["inspections", "furniture_items", "vehicles", "inspection_items"]

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
        inspections = fields.Dict(
            keys=fields.Str(),
            values=fields.Dict(
                keys=fields.Constant("inspection"),
                values=fields.Nested(InspectionViewSet.CreateSchema),
            ),
        )
        furniture_items = fields.Dict(
            keys=fields.Str(),
            values=fields.Dict(
                keys=fields.Constant("furniture"),
                values=fields.Nested(FurnitureViewSet.DefaultSchema),
            ),
        )
        vehicles = fields.Dict(
            keys=fields.Str(),
            values=fields.Dict(
                keys=fields.Constant("vehicle"),
                values=fields.Nested(VehicleViewSet.DefaultSchema),
            ),
        )

    # An ordered list of how to commit the relations to the database
    relations = [
        magic.Relation("furniture", model=Furniture, root=Property),
        magic.Relation("vehicle", model=Vehicle, root=Property, many=True),
        magic.Relation("inspection", model=Inspection, root=Property),
        magic.Relation("inspection_item", model=InspectionItem, root=Inspection),
    ]

    schemas = magic.SchemaContainer(
        "property",
        DefaultSchema,
        create=CreateSchema,
        relations=relations,
    )
