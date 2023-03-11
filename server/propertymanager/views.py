import pdb

import magic
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import Error as DatabaseError
from marshmallow import Schema, fields
from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from rest_framework.response import Response

from .models import Inspection, Property, User


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

    schemas = magic.SchemaContainer(
        DefaultSchema(), create=CreateSchema(), list=DefaultSchema(many=True)
    )
    schemas.add_dep("inspection", {"model": Inspection, "references": "property"})
