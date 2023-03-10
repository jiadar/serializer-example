import pdb
from importlib import import_module

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.paginator import Paginator
from django.db import Error as DatabaseError
from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from rest_framework import viewsets
from rest_framework.response import Response


def paginated_result(schema, paginator, page_number):
    page = paginator.get_page(page_number)
    data = schema.dump(page.object_list)
    result = {
        "data": data,
        "current_page": page.number,
        "has_next": page.has_next(),
        "has_previous": page.has_previous(),
        "next_page": page.next_page_number() if page.has_next() else None,
        "previous_page": page.previous_page_number() if page.has_previous() else None,
        "total_pages": paginator.num_pages,
        "total_records": paginator.count,
    }
    return result


class MarshmallowViewSet(viewsets.ViewSet):
    def list(self, request):
        schema = self.schemas.list
        queryset = self.model.objects.all().order_by(self.model.ORDER_BY)
        return Response(
            paginated_result(
                schema, Paginator(queryset, 5), request.query_params.get("page")
            )
        )

    def create(self, request):
        try:
            json = self.schemas.create.load(request.data)
        except MarshmallowValidationError as e:
            return Response({"message": f"Deserialization error: {e}"})

        if self.schemas.has_dependents:
            dep_spec = self.schemas.dependents[0]
            (key, model_class_str, schema_str) = dep_spec
            # check key in json
            # try / except here
            model_class = import_module(model_class_str, package=None)
            schema = model_class.get_attr(model_class, schema_str)
            dep_obj = json.get(key)
            # now try the below with dep_obj, inserting it, and do so recursively

        try:
            obj = self.model(**json)
        except DjangoValidationError as e:
            return Response({"message": f"Validation error: {e}"})

        try:
            obj.save()
        except DatabaseError as e:
            return Response({"message": f"Database error: {e}"})

        return Response({"message": "accepted"})


def schema_factory(default, **kwargs):
    schemas = {}
    for schema in ["list", "create", "retrieve", "update", "partial_update", "destroy"]:
        schemas[schema] = kwargs[schema] if schema in kwargs else default
    return type("SchemaContainer", (object,), schemas)
