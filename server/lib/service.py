from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms.utils import ErrorDict, ErrorList


class ServiceMetaclass(type):
    """Declartive metaclass for services

    Allow the service to be declarative by taking fields from the class, and put
    them in a dict of declared fields. Then remove those fields from the class attrs
    and create the class. Do this for any inherited classes as well.
    """

    def __new__(mcs, name, bases, attrs):
        attrs["declared_fields"] = {
            key: attrs.pop(key)
            for key, value in list(attrs.items())
            if isinstance(value, Field)
        }

        new_class = super().__new__(mcs, name, bases, attrs)

        declared_fields = {}
        for base in reversed(new_class.__mro__):
            if hasattr(base, "declared_fields"):
                declared_fields.update(base.declared_fields)
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_fields:
                    declared_fields.pop(attr)

        new_class.fields = declared_fields
        new_class.declared_fields = declared_fields

        return new_class


class BaseService:
    """Base class for services

    Takes the input to the service and validates it against the field definitions.
    Returns errors if the fields don't validate. Modeled off Django's forms, with the
    web stuff removed, as to be able to run in lib without importing anything from django.
    """

    def __init__(self, data=None, deps=None):
        self.is_bound = data is not None
        self.data = {} if data is None else data
        self.deps = {} if deps is None else deps
        self._errors = None

    def __repr__(self):
        if self._errors is None:
            is_valid = "Unknown"
        else:
            is_valid = self.is_bound and not self._errors
        return "<%(cls)s bound=%(bound)s, valid=%(valid)s, fields=(%(fields)s)>" % {
            "cls": self.__class__.__name__,
            "bound": self.is_bound,
            "valid": is_valid,
            "fields": ";".join(self.fields),
        }

    def _bound_items(self):
        for name in self.fields:
            yield name, self[name]

    def __iter__(self):
        for name in self.fields:
            yield self[name]

    def __getitem__(self, name):
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError(
                "Key '%s' not found in '%s'. Choices are: %s."
                % (
                    name,
                    self.__class__.__name__,
                    ", ".join(sorted(self.fields)),
                )
            )
        return field.get_bound_field(self, name)

    @property
    def errors(self):
        if self._errors is None:
            self.full_clean()
        return self._errors

    def is_valid(self):
        return self.is_bound and not self.errors

    def add_error(self, field, error):
        if not isinstance(error, ValidationError):
            error = ValidationError(error)

        if hasattr(error, "error_dict"):
            if field is not None:
                raise TypeError(
                    "The argument `field` must be `None` when the `error` "
                    "argument contains errors for multiple fields."
                )
            else:
                error = error.error_dict
        else:
            error = {field}

        for field, error_list in error.items():
            if field not in self.errors:
                if field not in self.fields:
                    raise ValueError(
                        "'%s' has no field named '%s'."
                        % (self.__class__.__name__, field)
                    )
                else:
                    self._errors[field] = ErrorList(renderer=self.renderer)
            self._errors[field].extend(error_list)
            if field in self.cleaned_data:
                del self.cleaned_data[field]

    def has_error(self, field, code=None):
        return field in self.errors and (
            code is None
            or any(error.code == code for error in self.errors.as_data()[field])
        )

    def clean(self):
        self._errors = ErrorDict()
        if not self.is_bound:
            return
        self.cleaned_data = {}
        for name, bf in self._bound_items():
            field = bf.field
            value = bf.initial if field.disabled else bf.data
            try:
                self.cleaned_data[name] = value
                if hasattr(self, "clean_%s" % name):
                    value = getattr(self, "clean_%s" % name)()
                    self.cleaned_data[name] = value
            except ValidationError as e:
                self.add_error(name, e)


class Service(BaseService, metaclass=ServiceMetaclass):
    """
    Allow specification of a service as a declarative class with fields. Subclass this
    and overwrite action with the required business logic. Then call ServiceClass(data)
    to execute the action.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self._provider = NoneProvider
        if self.hasattr("DEFAULT_PROVIDER"):
            self._provider = self.DEFAULT_PROVIDER
        if "provider" in kwargs:
            self._provider = kwargs["provider"]
        if not self.is_valid():
            raise ValidationError("Invalid data provided to service")
        for k, v in self.cleaned_data.items():
            self.__setattr__(k, v)
        with transaction.atomic():
            return self.action()

    def action(self):
        raise NotImplementedError("Subclass must implement service action method")


def create_service_class(provider):
    """Wraps the service class with the provider"""
    return type("Service", (Service,), {"DEFAULT_PROVIDER": provider})
