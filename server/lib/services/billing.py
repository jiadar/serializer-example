from django import forms
from lib.providers import StripeProvider
from lib.service import create_service_class

"""Billing Services

This provides all the actions that can take place with the billing provider. Written this way,
we can easily swap billing providers by making another provider class mapping to the new provider,
and ideally would not have to change this business logic.
"""

Service = create_service_class(StripeProvider)


class CreateAndFinalizeInvoice(Service):
    customer_id = forms.CharField()
    lineitem = forms.CharField()

    def action(self):
        self._provider.create_invoice(self.customer_id)
        self._provider.add_invoice_lineitem(self.lineitem)


class CreateStripeCustomer(Service):
    address = forms.TextField()
