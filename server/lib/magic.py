from marshmallow import Schema as MarshmallowSchema
from marshmallow.fields import Field


def create_schema_cls(model):
    """Some magic to attach the Django ORM model to the marshmallow schema"""
    return type("MagicSchema", (MarshmallowSchema,), {"model": model})


def field_repr(self):
    """Some magic to fix the fields repr to a sane, concise format

    Not stricly necessary but nice for debugging. This will run when we import magic from views.
    """
    return "<fields.{ClassName}>".format(ClassName=self.__class__.__name__, self=self)


Field().__class__.__repr__ = field_repr
