import pdb

from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import forms

from lib.providers import NoneProvider


class BaseService(forms.BaseForm):
    def __init__(self, *args, **kwargs):
        """
        Add the provider specified in kwargs (usually for mocks / testing). If there is
        no provider, use the default one specified when the service was created.
        """

        self._provider = None
        if "provider" in kwargs:
            self._provider = kwargs.pop("provider")
        super().__init__(*args, **kwargs)
        if hasattr(self, "_DEFAULT_PROVIDER") and not self._provider:
            self._provider = self._DEFAULT_PROVIDER
        if not self._provider:
            self._provider = NoneProvider

    @property
    def provider(self):
        return self._provider


class Service(BaseService, metaclass=forms.DeclarativeFieldsMetaclass):
    """
    Allow specification of a service as a declarative class with fields. Subclass this
    and overwrite action with the required business logic. Then call ServiceClass(data)
    to execute the action.
    """

    def svc_clean(self):
        if not self.is_valid():
            raise ValidationError(self.errors, self.non_field_errrors())

    @classmethod
    def exec(cls, *args, **kwargs):
        instance = cls(*args, **kwargs)
        instance.svc_clean()
        with transaction.atomic():
            return instance.action()

    def action(self):
        raise NotImplementedError("Subclass must implement service action method")


def create_service_class(provider):
    """Wraps the service class with the provider"""
    return type("Service", (Service,), {"_DEFAULT_PROVIDER": provider})
