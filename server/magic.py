import pdb
from collections.abc import MutableMapping
from contextlib import suppress
from importlib import import_module
from pprint import pprint as pp

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.paginator import Paginator
from django.db import Error as DatabaseError
from marshmallow import Schema as MarshmallowSchema
from marshmallow import fields
from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from marshmallow.fields import Field
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


class Node:
    def __init__(self, key, schema, raw):
        self.key = key
        self.model = schema.model
        self.schema = schema
        self.raw = raw
        self.nested_fields = {}
        self.parent = None
        self.children = []
        self.related = []
        self.obj = {}

        self.nested_fields = [
            k for k, v in self.schema.fields.items() if type(v) == fields.Nested
        ]

        for k, v in self.raw.items():
            if k in self.nested_fields:
                self.related.append({k: v})
            else:
                self.obj[k] = v

    def __repr__(self):
        return f"<Node {self.key}>"

    def dict(self):
        return {
            "key": self.key,
            "model": self.model,
            "schema": self.schema,
            "nested_fields": self.nested_fields,
            "parent": self.parent,
            "children": self.children,
            "obj": self.obj,
            "related": self.related,
        }

    def full_dict(self):
        return {
            "key": self.key,
            "model": self.model,
            "schema": self.schema,
            "nested_fields": self.nested_fields,
            "parent": self.parent,
            "children": self.children,
            "related": self.related,
            "raw": self.raw,
            "obj": self.obj,
        }

    def set_parent(self, parent):
        self.parent = parent

    def add_child(self, child):
        self.children.append(child)


class MarshmallowViewSet(viewsets.ViewSet):
    def create_objs(self, root_dict):
        root = Node("property", self.schemas.create, root_dict)

        for rel in root.related:
            key = next(iter(rel))
            sch = self.schemas.create.fields[key].schema
            if type(rel[key]) == list:
                for item in rel[key]:
                    child = Node(key, sch, item)
                    child.set_parent(root)
                    root.add_child(child)
            else:
                child = Node(key, sch, rel)
                child.set_parent(root)
                root.add_child(child)

        for intermediate in root.children:
            for rel in intermediate.related:
                key = next(iter(rel))
                sch = intermediate.schema.fields[key].schema
                if type(rel[key]) == list:
                    for item in rel[key]:
                        child = Node(key, sch, item)
                        child.set_parent(intermediate)
                        intermediate.add_child(child)
                else:
                    child = Node(key, sch, rel)
                    child.set_parent(intermediate)
                    intermediate.add_child(child)

        for intermediate in root.children:
            for final in intermediate.children:
                for rel in final.related:
                    key = next(iter(rel))
                    sch = final.schema.fields[key].schema
                    if type(rel[key]) == list:
                        for item in rel[key]:
                            child = Node(key, sch, item)
                            child.set_parent(final)
                            final.add_child(child)
                    else:
                        child = Node(key, sch, rel)
                        child.set_parent(final)
                        final.add_child(child)

        pdb.set_trace()

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

    def create(self, request):
        try:
            root_dict = self.schemas.create.load(request.data)
        except MarshmallowValidationError as e:
            return Response({"message": f"Deserialization error: {e}"})
        self.create_objs(root_dict)


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


def create_schema_cls(model):
    return type("MagicSchema", (MarshmallowSchema,), {"model": model})


class SchemaContainer:
    def _gen_schema(self, view, kwargs):
        return kwargs[view] if view in kwargs else self.default

    def __init__(self, default, **kwargs):
        self.default = default
        for view in [
            "list",
            "create",
            "retrieve",
            "update",
            "partial_update",
            "destroy",
        ]:
            sch_cls = self._gen_schema(view, kwargs)
            self.__setattr__(view, sch_cls())
        self.relations = []
        if "relations" in kwargs:
            for idx, relation in enumerate(kwargs["relations"]):
                relation.set_order(idx + 1)
                self.relations.append(relation)


def field_repr(self):
    return "<fields.{ClassName}>".format(ClassName=self.__class__.__name__, self=self)


Field().__class__.__repr__ = field_repr
