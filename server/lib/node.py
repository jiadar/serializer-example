from django.db import Error as DatabaseError
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor, ManyToManyDescriptor)
from inflector import Inflector
from marshmallow import fields
from rest_framework.response import Response


class Node:
    """A Node represents the full set of information necessary to handle nested json requests"""

    def __init__(self, schema, raw, key=None):
        """Initialize a node by processing raw data with a schema into a python object

        Required Arguments:
        schema -- The marshmallow schema used to convert this object from json to python
        raw -- The raw data from the request

        If not passed as kwarg, we calculate the key based off the name of the django model,
        lowercasing it. This helps us bootstrap the root object.

        We calculate the nested fields one level deep by looking for nested fields on the
        marshmallow schema.

        Then we derive the objects related to the current node based off those nested fields
        by removing the keys with those nested fields. This breaks up the nested dictionary
        into something we can process.

        If a field is static (not a nesting/relation), we add it to the pojo. The pojo contains
        the data necessary to create the django object using the django model. We don't create
        the object now though, because we could have a foreign key constraint error.
        """
        self.key = schema.model().__class__.__name__.lower() if key is None else key
        self.model = schema.model
        self.schema = schema
        self.raw = raw
        self.parent = None
        self.children = []
        self.related = []
        self.pojo = {}
        self.obj = None
        self.nested_fields = [
            k for k, v in self.schema.fields.items() if type(v) == fields.Nested
        ]

        for k, v in self.raw.items():
            if k in self.nested_fields:
                self.related.append({k: v})
            else:
                self.pojo[k] = v

    def __repr__(self):
        """Pretty print the essential Node details"""
        return f"<Node {self.key}>"

    @staticmethod
    def add_node(parent, rel):
        """Add a node to the already existing parent node by processing the related object

        The related object should only have one key, so we get the first key. We retreive it's
        marshmallow schema from the parent's fields. The nested schema is stored at key.schema.

        Next, we determine if the related data is a list or dictionary. If it is a list, we
        create a new child node for each element in the list, and add that to the parent. If
        it's a dictionary, we only add one child node.
        """
        key = next(iter(rel))
        sch = parent.schema.fields[key].schema
        if type(rel[key]) == list:
            for item in rel[key]:
                child = Node(sch, item, key=key)
                child.set_parent(parent)
                parent.add_child(child)
        else:
            child = Node(sch, rel, key=key)
            child.set_parent(parent)
            parent.add_child(child)

    @staticmethod
    def create_tree(cur):
        """A static method on the class will create a tree by exploring all children in the cur node.

        To do this, if the cur node has related (nested) objects, we add a node to the tree off as
        a child of the current node. After we've added all children at the current level of depth,
        we will recursively create_tree's for each of the children. Then we return the tree.
        """
        for rel in cur.related:
            Node.add_node(cur, rel)
        for child in cur.children:
            Node.create_tree(child)
        return cur

    def set_parent(self, parent):
        """Set the parent instance variable.

        If we have 1:many related keys like { inspections: [..., ...] } this won't map back to the
        django ORM object which conventionally would have a key { inspection: ...}. Therefore in the
        case of 1:many we will singularize the key so that the code handling these relationships
        works seamlessly.

        This assumes a certian way of setting up the models and schemas, so if things are not working
        as you might expect, this could be the source of the issue.
        """
        self.parent = parent
        if self.parent and self.isManyToOne(self.parent.key):
            self.key = Inflector().singularize(self.key)

    def add_child(self, child):
        """Add child to the list of my children"""
        self.children.append(child)

    def isManyToMany(self):
        """Determine if I am a many to many relationship

        To make this determination, I must have a parent and my key has to be in the parent's
        dictionary. For instance, if I am a property that has many vehicles and vehicles have many
        properties, you will be able to query property.vehicles. In this case, key is 'vehicles'
        and self.parent is 'property'. If the parent model contains the 'vehicles' key, then
        check the type, and if it's ManyToManyDescriptor then this is a Many:Many relation.
        """
        return (
            self.parent
            and self.parent.model
            and self.key in self.parent.model.__dict__
            and type(getattr(self.parent.model, self.key)) == ManyToManyDescriptor
        )

    def isManyToOne(self, key):
        """Determine if I am a many to one relationship

        To make this determination, I must have a foreign key in my model. For instance, if I'm
        an inspection and I'm asking if I have a ManyToOne relationship with property, 'property'
        is the key passed in. If my model has the 'property' key as a FK, then I'm a ManyToOne
        relation.
        """
        return (
            self.model
            and key in self.model.__dict__
            and type(getattr(self.model, key)) == ForwardManyToOneDescriptor
        )

    def save(self):
        """Save (only) this node's django object to the database with error handling"""
        try:
            self.obj.save()
        except DatabaseError as e:
            return Response({"message": f"Database error saving objects: {e}"})

    def commit(self):
        """Traverse the tree starting at my node and commit all the objects to the database.

        First we create the ORM object using the django model from the pojo. If this object is
        the root (there are no parents), then we can save it as there are no FK constraints at
        the root.

        Otherwise, if it's a ManyToMany relation, there is a join table. I can save the ORM
        object to the database and THEN add rows to that join table via the parent ORM object.

        Otherwise, if it's a ManyToOne relation using the parent key as a FK, there will be a
        db constraint. Therefore, add the object to myself by setting the parent pk on the
        proper field.

        Finally, if I have children, recursively process each of them.
        """
        self.obj = self.model(**self.pojo)
        if not self.parent:
            self.save()
        if self.isManyToMany():
            self.save()
            self.parent.obj.__getattribute__(self.key).add(self.obj)
        if self.parent and self.isManyToOne(self.parent.key):
            self.obj.__setattr__(self.parent.key, self.parent.obj)
            self.save()
        if len(self.children) > 0:
            [child.commit() for child in self.children]
