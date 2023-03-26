from magic import Service

"""App-Level Services

Services can apply to multiple models, no models, and potentially have external side effects.
If the logic required applies to multiple models within this app, or has call-outs to 3rd party
and other side effects required by this app, it should go here.

Services should not deal with request/response, only the data necessary to perform the
business logic should be passed. Services should not depend on or require a database, though
it can work with Django ORM objects.

If services call out to 3rd parties, any methods that do should allow injection of the 3rd
party (for instance from lib/stripe.py). The real service could be injected by default for
integration and production, while a mock service could be provided for unit tests.

"""


class PropertyManagerService(Service):
    pass
