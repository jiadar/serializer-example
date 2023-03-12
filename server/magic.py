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
        # Try to turn the json data received into a nested django ORM *root* object
        try:
            root_obj = self.schemas.create.load(request.data)
        except MarshmallowValidationError as e:
            return Response({"message": f"Deserialization error: {e}"})

        # Make a list of child objects by extracting all the related objects
        # from the nested objects. We should be left with the primary *root* object
        children = []
        for relation in self.schemas.relations:
            if relation.key in root_obj:
                items = (
                    root_obj.pop(relation.key)
                    if isinstance(root_obj[relation.key], list)
                    else [root_obj.pop(relation.key)]
                )
                children.extend([item | {"_relation": relation} for item in items])

        # Now try to create the *root* object first. We need the root object created
        # in order to add dependent objects.
        try:
            root_obj = self.model(**root_obj)
        except DjangoValidationError as e:
            return Response({"message": f"Validation error: {e}"})

        # Try to save the root object to the database
        try:
            root_obj.save()
        except DatabaseError as e:
            return Response({"message": f"Database error saving primary object: {e}"})

        # Attach the child objects to the root object. If the object is a 1:many we attach
        # the root object onto the child object, then we save the child object.
        # If it's a many:many, we attach the possibly many objects to the root object
        # after saving the child object.
        try:
            for child in children:
                relation = child.pop("_relation")
                child_obj = relation.model(**child)
                if not relation.many:
                    child_obj.__setattr__(relation.related_field, root_obj)
                child_obj.save()
                if relation.many:
                    root_obj.__getattribute__(relation.related_field).add(child_obj)
        except DatabaseError as e:
            return Response({"message": f"Database error saving related objects: {e}"})

        return Response({"message": "accepted"})


class Relation:
    def __init__(self, key, **kwargs):
        self.key = key
        self.model = kwargs["model"] if "model" in kwargs else key.capitalize()
        if "related_field" in kwargs:
            self.related_field = kwargs["related_field"]
        else:
            # todo - calculate from django model
            self.related_field = None
        if "many" in kwargs:
            self.many = kwargs["many"]
        else:
            # todo - calculate from django model
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
