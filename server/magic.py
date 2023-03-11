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

        objs = []
        for key, dep in self.schemas.deps.items():
            model = dep["model"]
            references = dep["references"]
            if key in json:
                dep_json = json.pop(key)
                dep_json[f"{references}_id"] = json[f"{references}_id"]
                related_obj = model(**dep_json)
                objs.append(related_obj)

        try:
            obj = self.model(**json)
        except DjangoValidationError as e:
            return Response({"message": f"Validation error: {e}"})

        try:
            obj.save()
        except DatabaseError as e:
            return Response({"message": f"Database error saving primary object: {e}"})

        try:
            for related_obj in objs:
                related_obj.save()
        except DatabaseError as e:
            return Response({"message": f"Database error saving related objects: {e}"})

        #        for obj in objs:
        #            obj.delete()
        #        obj.delete()
        return Response({"message": "accepted"})


class SchemaContainer:
    deps = {}

    def __init__(self, default, **kwargs):
        self.list = kwargs["list"] if "list" in kwargs else default
        self.create = kwargs["create"] if "create" in kwargs else default
        self.retrieve = kwargs["retrieve"] if "retrieve" in kwargs else default
        self.update = kwargs["update"] if "update" in kwargs else default
        self.partial_update = (
            kwargs["partial_update"] if "partial_update" in kwargs else default
        )
        self.destroy = kwargs["destroy"] if "destroy" in kwargs else default

    def add_dep(self, key, dep):
        self.deps[key] = dep
