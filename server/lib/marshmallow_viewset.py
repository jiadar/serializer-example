from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from rest_framework import viewsets
from rest_framework.response import Response
from lib.node import Node


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

    def retrieve(self, request, args, kwargs):
        """TBD

        This should work similarly to create, where we will recursively trace the 'list' schema
        and build up the return data by generating querysets for the root and nested data.
        """
        from pprint import pprint as pp

        schema = self.schemas.retrieve
        instance = schema.model.objects.get(pk=kwargs["pk"])
        json = schema.dump(instance)


        for field in instance.__dict__:
            # print(field)
            if str(instance.__dict__[field]) == kwargs["pk"]:
                instance_key = field


        # check for nested fields
        for key in schema.fields:
            if str(schema.fields[key]) == '<fields.Nested>':
                subschema = schema.fields[key].nested(many=True)
                #remove underscore character from key
                pk_key = key.replace("_", "")
                #remove the s from the end of the key to get the pk key
                pk_key = pk_key[:-1]
                qs = instance.__getattribute__(f"{pk_key}_set").all()
                json[key] = subschema.dump(qs)

                idx = 0
                for subinstance in qs:
                    for field in subschema.fields:
                        if str(subschema.fields[field]) == '<fields.Nested>':
                            subschema2 = subschema.fields[field].nested(many=True)
                            pk_key2 = field.replace("_", "")
                            pk_key2 = pk_key2[:-1]
                            qs2 = subinstance.__getattribute__(f"{pk_key2}_set").all()
                            json[key][idx][field] = subschema2.dump(qs2)
                            idx += 1


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
