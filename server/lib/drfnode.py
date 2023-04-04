from marshmallow import fields
from pprint import pprint as pp

class DNode:
    """A node that contains a django object and marshmallow schema use to build a json tree of nested objects"""

    def __init__(self, schema, obj, json=None):
        self.obj = obj
        self.schema = schema
        if json:
            self.json = json
        else:
            self.json = schema.dump(obj)
        self.parent = None
        self.children = []
        self.nested_fields = [
            k for k, v in self.schema.fields.items() if type(v) == fields.Nested
        ]

    def create_tree(self):
        for field in self.nested_fields:
            #remove trailing 's' from key
            pk_key = field[:-1].lower()
            #remove '_' from key
            pk_key = pk_key.replace("_", "")
            idx = 0
            self.json[field] = []
            for child in self.obj.__getattribute__(f"{pk_key}_set").all():
                child_node = DNode(self.schema.fields[field].nested(many=False), child)
                child_node.parent = self
                self.children.append(child_node)
                self.json[field].append(child_node.json)
                idx += 1
        for child in self.children:
            child.create_tree()
        return self

    def create_many_to_many(self, schema=None, keys=None):
        if keys is not None and schema is not None:
            for key in keys:
                try:
                    if str(type(self.obj.__getattribute__(key))) == "<class 'django.db.models.fields.related_descriptors.create_forward_many_to_many_manager.<locals>.ManyRelatedManager'>":

                        subschema = schema.fields[key].nested(many=True)
                        #remove trailing 's' from key
                        pk_key = key[:-1]
                        subinstances = self.obj.__getattribute__(key).all()
                        sub_json = subschema.dump(subinstances)
                        self.json[pk_key] = sub_json
                except:
                    pass
            for child in self.children:
                child.create_many_to_many()
            return self
