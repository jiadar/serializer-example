import pdb
from collections.abc import MutableMapping
from contextlib import suppress
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


def delete_keys(obj, keys):
    keys_set = set(keys)

    modified_dict = {}
    for key, value in obj.items():
        if key not in keys_set:
            if isinstance(value, MutableMapping):
                modified_dict[key] = delete_keys(value, keys_set)
            else:
                modified_dict[key] = value
    return modified_dict


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

        for item in result:
            for index, relation in enumerate(relations):
                if relation.key in item:
                    if "_relation" not in item[relation.key]:
                        item[relation.key]["_relation"] = {}
                    item[relation.key]["_relation"] = relation

        return result

    # not getting inspection item
    # need to go through ordering for insertion and better spec that
    # need to get property by itself
    def _get_order(self, obj_list, depth=0):
        res = []
        rels = {r.key: r.order for r in self.schemas.relations}
        for obj in obj_list:
            for key in obj.keys():
                # Zero depth should not have relations
                if "_relation" not in obj[key] and depth == 0:
                    res.append(obj)
                if "_relation" in obj[key] and depth == obj[key]["_relation"].order:
                    res.append(obj)
        return res

    def _flatten(self, obj, depth=0):
        key = next(iter(obj))
        if "_relation" in obj[key]:
            rels = [
                relation.key for relation in self.schemas.relations
            ] + self.nested_fields
            rels.remove(key)
            return delete_keys(obj, rels)
        else:
            return delete_keys(obj, self.nested_fields)

    def create(self, request):
        try:
            root_dict = self.schemas.create.load(request.data)
        except MarshmallowValidationError as e:
            return Response({"message": f"Deserialization error: {e}"})
        res = self._extract_elements(root_dict, self.schemas.relations)
        flat = [self._flatten(i) for i in res]
        ord = [
            self._get_order(flat, i) for i in range(0, len(self.schemas.relations) + 1)
        ]
        # needs try/except
        obj_dict = ord.pop(0)[0][self.root_key]
        root_obj = self.model(**obj_dict)
        root_obj.save()
        for lst in ord:
            key = next(iter(lst[0]))
            model = lst[0][key]["_relation"].model
            related_field = lst[0][key]["_relation"].root
            for item in lst:
                del item[key]["_relation"]
            raw_dict = [item[key] for item in lst]
            objs = [model(**item) for item in raw_dict]
            for obj in objs:
                if self.model == related_field:
                    print(f"Setting {self.root_key} on {key}")
                    obj.__setattr__(self.root_key, root_obj)
                else:
                    print(f"Setting fk on {key}")
                    pdb.set_trace()
                obj.save()
        return Response({"message": "accepted"})
        # return self._process(root_obj["property"])


class Relation:
    def __init__(self, key, **kwargs):
        self.key = key
        self.model = kwargs["model"] if "model" in kwargs else key.capitalize()
        if "root" in kwargs:
            self.root = kwargs["root"]
        else:
            # todo - calculate from django model
            self.root = None
        if "many" in kwargs:
            self.many = kwargs["many"]
        else:
            # todo - calculate from django model
            self.many = None
        self.order = kwargs["order"] if "order" in kwargs else 0

    def __repr__(self):
        return f"key={self.key}, order={self.order}, many={self.many}"

    def set_order(self, order):
        self.order = order


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
        self.relations = []
        if "relations" in kwargs:
            for idx, relation in enumerate(kwargs["relations"]):
                relation.set_order(idx + 1)
                self.relations.append(relation)
