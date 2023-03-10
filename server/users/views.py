import magic

from .models import User


class UserViewSet(magic.MarshmallowViewSet):
    model = User
    schemas = magic.schema_factory(
        User.schema.default(), list=User.schema.default(many=True)
    )
