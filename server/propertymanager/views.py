import pdb

import magic
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import Error as DatabaseError
from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from rest_framework.response import Response

from .models import Inspection, Property, User


class UserViewSet(magic.MarshmallowViewSet):
    model = User
    schemas = magic.schema_factory(
        User.schema.default(), list=User.schema.default(many=True)
    )


class PropertyViewSet(magic.MarshmallowViewSet):
    model = Property
    schemas = magic.schema_factory(
        Property.schema.default(),
        list=Property.schema.list(many=True),
        create=Property.schema.create(),
    )

    def create(self, request):
        try:
            json = self.schemas.create.load(request.data)
        except MarshmallowValidationError as e:
            return Response({"message": f"Deserialization error: {e}"})

        try:
            pdb.set_trace()
            inspector = User.objects.get(pk=json["inspection"]["inspector"])
            inspection = Inspection(**json["inspection"] | {"inspector": inspector})
            property = self.model(**json["property"])
        except DjangoValidationError as e:
            return Response({"message": f"Validation error: {e}"})

        try:
            pdb.set_trace()
            inspection.save()
            property.save()
        except DatabaseError as e:
            return Response({"message": f"Database error: {e}"})

        return Response({"message": "accepted"})


class InspectionViewSet(magic.MarshmallowViewSet):
    model = Inspection
    schemas = magic.schema_factory(
        Inspection.schema.default(),
        create=Inspection.schema.create(),
        list=Inspection.schema.default(many=True),
    )
