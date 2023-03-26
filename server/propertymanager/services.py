from lib.providers import NoneProvider
from lib.service import Service

"""App-Level Services

App-Level services can apply to multiple models, and potentially have external
side effects. If the logic required applies to multiple models within this app,
or has call-outs to 3rd party and other side effects required by this app, it should go here.

The key for services placed here is that it *must* use multiple models in the app (if it only
uses one model in this app, it should go in the manager or model). If it doesn't rely on this
app but rather is a generic thing in and of it's own, which could potentially be used by multiple
apps, it should go in lib/services.

Services should not deal with request/response, only the data necessary to perform the
business logic should be passed. Services should not depend on or require a database, though
it can work with Django ORM objects.

If services call out to 3rd parties, any methods that do should allow injection of the 3rd
party (for instance from lib/stripe.py). The real service could be injected by default for
integration and production, while a mock service could be provided for unit tests.

"""


class ProviderMixin:
    DEFAULT_PROVIDER = NoneProvider


class PropertyManagerService(ProviderMixin, Service):
    pass
