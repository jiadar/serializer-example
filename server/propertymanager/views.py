import magic
from marshmallow import fields
from marshmallow_viewset import MarshmallowViewSet
from schema_container import SchemaContainer

from .models import (Detail, Furniture, Inspection, InspectionItem, Property,
                     User, Vehicle)


class UserViewSet(MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(User)

    class DefaultSchema(schema_cls):
        user_id = fields.UUID()
        email = fields.Email()
        phone = fields.String()
        dob = fields.Date()
        address = fields.String()
        city = fields.String()
        state = fields.String()
        zip = fields.Number()

    schemas = SchemaContainer(DefaultSchema)


class FurnitureViewSet(MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(Furniture)

    class DefaultSchema(schema_cls):
        furniture_id = fields.UUID()
        description = fields.String()
        condition = fields.Number()
        inservice_date = fields.Date()
        expected_life = fields.Number()

    schemas = SchemaContainer(DefaultSchema)


class VehicleViewSet(MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(Vehicle)

    class DefaultSchema(schema_cls):
        vehicle_id = fields.UUID()
        make = fields.String()
        model = fields.String()
        year = fields.Number()
        description = fields.String()
        last_maintenance = fields.Date()

    schemas = SchemaContainer(DefaultSchema)


class DetailViewSet(MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(Detail)

    class DefaultSchema(schema_cls):
        detail_id = fields.UUID()
        description = fields.String()

    schemas = SchemaContainer(DefaultSchema)


class InspectionItemViewSet(MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(InspectionItem)

    class DefaultSchema(schema_cls):
        inspection_item_id = fields.UUID()
        description = fields.String()
        details = fields.Nested(DetailViewSet.DefaultSchema, many=True)

    schemas = SchemaContainer(DefaultSchema)


class InspectionViewSet(MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(Inspection)

    class DefaultSchema(schema_cls):
        inspection_id = fields.UUID()
        inspector = fields.UUID()
        inspection_date = fields.Date()
        findings = fields.String()

    class CreateSchema(schema_cls):
        inspection_id = fields.UUID()
        inspector_id = fields.UUID()
        inspection_date = fields.Date()
        findings = fields.String()
        inspection_items = fields.Nested(InspectionItemViewSet.DefaultSchema, many=True)

    schemas = SchemaContainer(
        DefaultSchema,
        create=CreateSchema,
    )


class PropertyViewSet(MarshmallowViewSet):
    schema_cls = magic.create_schema_cls(Property)

    class DefaultSchema(schema_cls):
        property_id = fields.UUID()
        owner_id = fields.UUID()
        address = fields.String()
        city = fields.String()
        state = fields.String()
        zip = fields.Number()
        description = fields.String()
        rent = fields.Number()

    class CreateSchema(schema_cls):
        property_id = fields.UUID()
        owner_id = fields.UUID()
        address = fields.String()
        city = fields.String()
        state = fields.String()
        zip = fields.Number()
        description = fields.String()
        rent = fields.Number()
        inspections = fields.Nested(InspectionViewSet.CreateSchema, many=True)
        furniture_items = fields.Nested(FurnitureViewSet.DefaultSchema, many=True)
        vehicles = fields.Nested(VehicleViewSet.DefaultSchema, many=True)

    schemas = SchemaContainer(
        DefaultSchema,
        create=CreateSchema,
    )
