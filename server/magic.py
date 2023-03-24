import pdb
from collections.abc import MutableMapping
from contextlib import suppress
from importlib import import_module
from pprint import pprint as pp

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.paginator import Paginator
from django.db import Error as DatabaseError
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor, ManyToManyDescriptor)
from inflector import Inflector
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


def save_to_database(obj):
    print(f"Saving {obj}...")
    try:
        obj.save()
    except DatabaseError as e:
        return Response({"message": f"Database error saving objects: {e}"})


class Node:
    def __init__(self, key, schema, raw):
        self.key = key
        self.model = schema.model
        self.schema = schema
        self.raw = raw
        self.parent = None
        self.children = []
        self.related = []
        self.pojo = {}  # Dictionary processed by marshmallow
        self.obj = None  # Django ORM object
        self.nested_fields = [
            k for k, v in self.schema.fields.items() if type(v) == fields.Nested
        ]

        for k, v in self.raw.items():
            if k in self.nested_fields:
                self.related.append({k: v})
            else:
                self.pojo[k] = v

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
            "pojo": self.pojo,
            "obj": self.obj,
            "related": self.related,
        }

    def set_parent(self, parent):
        self.parent = parent
        if self.parent and self.isManyToOne(self.parent.key):
            self.key = Inflector().singularize(self.key)

    def add_child(self, child):
        self.children.append(child)

    def isManyToMany(self):
        return (
            self.parent
            and self.parent.model
            and self.key in self.parent.model.__dict__
            and type(getattr(self.parent.model, self.key)) == ManyToManyDescriptor
        )

    def isManyToOne(self, key):
        return (
            self.model
            and key in self.model.__dict__
            and type(getattr(self.model, key)) == ForwardManyToOneDescriptor
        )

    @staticmethod
    def _get_leaves(cur, res):
        if len(cur.children) == 0:
            res.append(cur)
        for child in cur.children:
            Node._get_leaves(child, res)
        return res

    def leaves(self):
        return Node._get_leaves(self, [])

    @staticmethod
    def add_node(parent, rel):
        key = next(iter(rel))
        sch = parent.schema.fields[key].schema
        if type(rel[key]) == list:
            for item in rel[key]:
                child = Node(key, sch, item)
                child.set_parent(parent)
                parent.add_child(child)
        else:
            child = Node(key, sch, rel)
            child.set_parent(parent)
            parent.add_child(child)

    @staticmethod
    def create_tree(cur):
        for rel in cur.related:
            Node.add_node(cur, rel)
        for child in cur.children:
            Node.create_tree(child)
        return cur

    def commit(self):
        self.obj = self.model(**self.pojo)
        pdb.set_trace()
        if not self.parent:
            save_to_database(self.obj)
        if self.isManyToMany():
            print(f"Adding many to many relationship {self.key} to {self.parent}")
            save_to_database(self.obj)
            self.parent.obj.__getattribute__(self.key).add(self.obj)
        if self.parent and self.isManyToOne(self.parent.key):
            print(f"Adding foreign key from {self.key} to {self.parent}")
            self.obj.__setattr__(self.parent.key, self.parent.obj)
            save_to_database(self.obj)
        if len(self.children) > 0:
            [child.commit() for child in self.children]


class MarshmallowViewSet(viewsets.ViewSet):
    def validate(self, json):
        try:
            root_dict = self.schemas.create.load(json)
        except MarshmallowValidationError as e:
            return Response({"message": f"Deserialization error: {e}"})
        return root_dict

    def list(self, request):
        schema = self.schemas.list
        queryset = self.model.objects.all().order_by(self.model.ORDER_BY)
        return Response(
            paginated_result(
                schema, Paginator(queryset, 5), request.query_params.get("page")
            )
        )

    def create(self, request):
        root_dict = self.validate(request.data)
        root = Node.create_tree(Node("property", self.schemas.create, root_dict))
        root.commit()
        pdb.set_trace()
        # try:
        #     root.obj = root.model(**root.pojo)
        # except DjangoValidationError as e:
        #     return Response({"message": f"Validation error: {e}"})

        # try:
        #     root.obj.save()
        # except DatabaseError as e:
        #     return Response({"message": f"Database error saving primary object: {e}"})

        # for child in root.children:
        #     child.commit()

        # intermediate = [c.children for c in root.children]
        # for children in intermediate:
        #     for child in children:
        #         print(f"Processing {child}...")
        #         child.commit()

        # final = [[c.children for c in lst] for lst in intermediate]
        # for lst in final:
        #     for children in lst:
        #         for child in children:
        #             print(f"Processing {child}...")
        #             child.commit()
        #             pdb.set_trace()

        return Response({"message": "accepted"})


class Relation:
    def __init__(self, key, **kwargs):
        self.key = key
        self.model = kwargs["model"] if "model" in kwargs else key.capitalize()
        if "root" in kwargs:
            self.root = kwargs["root"]
        else:
            self.root = None
        if "many" in kwargs:
            self.many = kwargs["many"]
        else:
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
