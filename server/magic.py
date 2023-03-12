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

        for rel in self.schemas.relations:
            if rel.key in json:
                rel_json = json.pop(rel.key)
                if not isinstance(rel_json, list):
                    rel_json = [rel_json]
                for item in rel_json:
                    related_obj = rel.model(**item)
                    objs.append((related_obj, rel.related_field, rel.many))

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
                (related_model_instance, related_field, many) = related_obj
                print(type(related_model_instance))
                pdb.set_trace()
                if not many:
                    related_model_instance.__setattr__(related_field, obj)
                related_model_instance.save()
                if many:
                    obj.__getattribute__(related_field).add(related_model_instance)
        except DatabaseError as e:
            return Response({"message": f"Database error saving related objects: {e}"})

        return Response({"message": "accepted"})


class Relation:
    def __init__(self, key, **kwargs):
        self.key = key
        self.model = kwargs["model"] if "model" in kwargs else key.capitalize()
        if kwargs["related_field"]:
            self.related_field = kwargs["related_field"]
        else:
            # calculate from django model
            self.related_field = None
        if "many" in kwargs:
            self.many = kwargs["many"]
        else:
            # calculate from django model
            self.many = None


class SchemaContainer:
    def __init__(self, default, **kwargs):
        self.list = kwargs["list"] if "list" in kwargs else default
        self.create = kwargs["create"] if "create" in kwargs else default
        self.retrieve = kwargs["retrieve"] if "retrieve" in kwargs else default
        self.update = kwargs["update"] if "update" in kwargs else default
        self.partial_update = (
            kwargs["partial_update"] if "partial_update" in kwargs else default
        )
        self.destroy = kwargs["destroy"] if "destroy" in kwargs else default
        self.relations = kwargs["relations"] if "relations" in kwargs else []

    def relation(key):
        return next((x for x in _relations if x.key == key), None)
