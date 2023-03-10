import magic

from .models import Property


class PropertyViewSet(magic.MarshmallowViewSet):
    model = Property
    schemas = magic.schema_factory(
        Property.schema.default(), list=Property.schema.list(many=True)
    )
