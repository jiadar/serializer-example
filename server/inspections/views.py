import magic

from .models import Inspection


class InspectionViewSet(magic.MarshmallowViewSet):
    model = Inspection
    schemas = magic.schema_factory(
        Inspection.schema.default(),
        create=Inspection.schema.create(),
        list=Inspection.schema.default(many=True),
    )
