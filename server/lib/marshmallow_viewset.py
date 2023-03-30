from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError
from rest_framework import viewsets
from rest_framework.response import Response
from pprint import pprint as pp
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
        from propertymanager.views import DetailViewSet as dvs
        from propertymanager.models import Detail
        # from propertymanager.models import InspectionItem
        # schema = self.schemas.retrieve
        schema = dvs.DetailSchema()

        instance = Detail.objects.get(pk=kwargs["pk"])
        json = schema.dump(instance)


        # import pdb; pdb.set_trace();
        # vehicles = instance.vehicles.all()
        # json["vehicles"] = schema.dump(vehicles, many=True)
        # inspections = instance.inspection_set.all()
        # schema.dump(inspections,many=True)
        
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
