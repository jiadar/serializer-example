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


class EmailProvider:
    @classmethod
    def send_email(cls, template, email, data):
        # call 3rd party service
        return {"status": "ok"}


class MockEmailProvider:
    @classmethod
    def send_email(cls, template, email, data):
        # return response that the 3rd party api would return, but don't actually call out
        return {"status": "ok"}


class NoneProvider:
    # Generic provider that will respond to any method and return an error
    pass
