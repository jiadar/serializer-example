"""
Define the providers to use in the services.

In a larger app, this could be a directory with modules for each provider.
"""


class SendgridProvider:
    @classmethod
    def send_email(template, email):
        # call 3rd party service
        pass


class StripeProvider:
    @classmethod
    def create_invoice(customer_id):
        # call 3rd party service
        pass

    @classmethod
    def add_invoice_lineitem(lineitem):
        # call 3rd party service
        pass


class MockSendgridProvider:
    @classmethod
    def send_email(template, email):
        # return response that the 3rd party would return, but don't actually call out
        pass
