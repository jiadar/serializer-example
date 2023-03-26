from django import forms

from magic import SendgridProvider, Service, StripeProvider

"""Umbrella Services

Services that require multiple apps or otherwise necessitate multiple parts of the system
to perform business logic or cause side effects.

This should ideally live in lib/ and import any standalone django apps or other code as necessary.
This could/should also be a directory as the file grows - different logic can be separated into
files/python packages as appropriate.

These services can apply to multiple django apps, no django apps, and potentially have external
side effects.

Services should not deal with request/response, only the data necessary to perform the
business logic should be passed. Services should not depend on or require a database, though
it can work with Django ORM objects.

If services call out to 3rd parties, any methods that do should allow injection of the 3rd
party (for instance from lib/providers/stripe.py). The real service could be injected by default for
integration and production, while a mock service could be provided for unit tests.

"""


class EmailService(Service):
    template = forms.CharField()
    email = forms.EmailField()

    DEFAULT_PROVIDER = SendgridProvider

    def action(self):
        self._provider.send_email(self.template, self.email)


class CreateAndFinalizeInvoice(Service):
    customer_id = forms.CharField()
    lineitem = forms.CharField()

    DEFAULT_PROVIDER = StripeProvider

    def action(self):
        self._provider.create_invoice(self.customer_id)
        self._provider.add_invoice_lineitem(self.lineitem)
