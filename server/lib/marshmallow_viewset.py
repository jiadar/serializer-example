from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from rest_framework import viewsets
from rest_framework.response import Response
from lib.node import Node
from django.db.models.fields.related_descriptors import (ManyToManyDescriptor)

class MarshmallowViewSet(viewsets.ViewSet):
    """
    An DRF powered viewset using marshmallow schemas and a tree to allow arbitrary nesting of
    objects. Typically we will want nesting in retreive, list, and create endpoints. Though similar
    strategies used with create could be applied to any endpoint.
    """

    def validate(self, json):
        """Validate the json data passed is valid via the marshmallow schema

        If it is, deserialize it and return the python dict object. Otherwise, return an error.
        """
        try:
            root_dict = self.schemas.create.load(json)
        except MarshmallowValidationError as e:
            return Response({"message": f"Deserialization error: {e}"})
        return root_dict

    def get_nested_schemas(self, schema):
        subschemas = []
        for key in schema.fields:
            if str(schema.fields[key]) == '<fields.Nested>':
                subschema = schema.fields[key].nested(many=True)
                subschemas.append(subschema)
        return subschemas

    def dump_nested(self, schema, instance, json):
        subschemas = self.get_nested_schemas(schema)
        for subschema in subschemas:
            pk_key = subschema.model.__name__.lower()
            qs = instance.__getattribute__(f"{pk_key}_set").all()
            sub_json = subschema.dump(qs)
            idx = 0
            for subinstance in qs:
                self.dump_nested(subschema, subinstance, sub_json[idx])
                idx += 1
            json[pk_key] = sub_json

    def dump_many_to_many(self, schema, instance, json):
        for key in schema.fields:
            try:
                if str(type(instance.__getattribute__(key))) == "<class 'django.db.models.fields.related_descriptors.create_forward_many_to_many_manager.<locals>.ManyRelatedManager'>":
                    subschema = schema.fields[key].nested(many=True)
                    #remove trailing 's' from key
                    pk_key = key[:-1]
                    subinstances = instance.__getattribute__(key).all()
                    sub_json = subschema.dump(subinstances)
                    json[pk_key] = sub_json
            except:
                pass


    def retrieve(self, request, args, kwargs):
        """TBD

        This should work similarly to create, where we will recursively trace the 'list' schema
        and build up the return data by generating querysets for the root and nested data.
        """
        from pprint import pprint as pp
        schema = self.schemas.retrieve
        instance = schema.model.objects.get(pk=kwargs["pk"])

        json = schema.dump(instance)
        self.dump_nested(schema, instance, json)
        # import pdb; pdb.set_trace();
        self.dump_many_to_many(self.schemas.create, instance, json)

        #hard coded vehicles for now
        # from propertymanager.views import VehicleViewSet as vvs
        # vschema = vvs.DefaultSchema()
        # vehicles = instance.vehicles.all()
        # json["vehicles"] = vschema.dump(vehicles, many=True)
        return Response(json)

    def list(self, request):
        """TBD

        This will work like retreive, but operate on multiple items.
        """
        pass

    def create(self, request):
        root_dict = self.validate(request.data)
        Node.create_tree(Node(self.schemas.create, root_dict)).commit()
        return Response(root_dict)
