import pdb
from importlib import import_module
from pprint import pprint as pp

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.paginator import Paginator
from django.db import Error as DatabaseError
from marshmallow import Schema, fields
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

    def _process(self, root_obj):
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
                _process(child_obj)
                if not relation.many:
                    child_obj.__setattr__(relation.related_field, root_obj)
                child_obj.save()
                if relation.many:
                    root_obj.__getattribute__(relation.related_field).add(child_obj)
        except DatabaseError as e:
            return Response({"message": f"Database error saving related objects: {e}"})

        return Response({"message": "accepted"})

    def _extract_elements(self, json, relations, result=[]):
        root_key = "property"
        relation_keys = [item.key for item in relations] + [root_key]
        result = []

        def _get_related(json):
            if isinstance(json, dict):
                for k, v in json.items():
                    if k in relation_keys:
                        result.append({k: v})
                    _get_related(v)

        _get_related(json)

        def _delete_nested(json, keys, depth=0):
            if depth > 0:
                for key in keys:
                    if key in json.keys():
                        json.pop(key)
            for v in json.values():
                if isinstance(v, dict):
                    _delete_nested(v, keys, depth + 1)

        pruned_result = [_delete_nested(item, self.nested_fields) for item in result]

        for item in result:
            for index, relation in enumerate(relations):
                if relation.key in item:
                    if "_internal" not in item[relation.key]:
                        item[relation.key]["_internal"] = {}
                    internal = item[relation.key]["_internal"]
                    internal["relation"] = relation
                    internal["key"] = relation.key
                    internal["model"] = relation.model
                    internal["related_field"] = relation.related_field
                    internal["order"] = index
        return result

    # not getting inspection item
    # need to go through ordering for insertion and better spec that
    def _get_order(self, objs, depth=0):
        res = []
        for item in objs:
            key = next(iter(item))
            if depth == 0 and "_internal" not in item[key]:
                return [item]
            if "_internal" in item[key] and depth == item[key]["_internal"]["order"]:
                res.append(item)
        return res

    def create(self, request):
        try:
            root_obj = self.schemas.create.load(request.data)
        except MarshmallowValidationError as e:
            return Response({"message": f"Deserialization error: {e}"})
        res = self._extract_elements(root_obj, self.schemas.relations)
        ord = self._get_order(res, 3)
        pdb.set_trace()
        return Response({"message": "accepted"})
        # return self._process(root_obj["property"])


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
    def _wrap(self, view, schema):
        name = f"{self.root_key.capitalize()}{view.capitalize()}Schema".replace("_", "")
        wrapped_schema = Schema.from_dict(
            {self.root_key: fields.Nested(schema)},
            name=name,
        )
        return wrapped_schema

    def _gen_schema(self, view, kwargs):
        return (
            self._wrap(view, kwargs[view])
            if view in kwargs
            else self._wrap(view, self.default)
        )

    def __init__(self, root_key, default, **kwargs):
        self.root_key = root_key
        self.default = self._wrap("default", default)
        for view in [
            "list",
            "create",
            "retrieve",
            "update",
            "partial_update",
            "destroy",
        ]:
            wrapped_schema = self._gen_schema(view, kwargs)
            self.__setattr__(view, wrapped_schema())
        self.relations = kwargs["relations"] if "relations" in kwargs else []

    def relation(key):
        return next((x for x in _relations if x.key == key), None)
