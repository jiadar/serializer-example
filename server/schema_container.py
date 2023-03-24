import pdb


class SchemaContainer:
    """A container to hold marshmallow schemas for all DRF operations.

    This could have just been a dictionary, but this allows us to easily re-use schemas
    for different DRF endpoints if we'd like to. It also makes the Nodes which hold
    the schemas more concise.
    """

    def _gen_schema(self, view, kwargs):
        """Generate a schema using the default if a schema for the view does not exist"""
        return kwargs[view] if view in kwargs else self.default

    def __init__(self, default, **kwargs):
        """Ensure that all DRF views have an associated instantiated schema

        Do some magic at the end to prepend the model to the schema name for clarity
        """
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
            instance = sch_cls()
            instance.__class__.__name__ = (
                f"{instance.model().__class__.__name__}{instance.__class__.__name__}"
            )
            self.__setattr__(view, instance)
