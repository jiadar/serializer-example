from django import forms
from lib.providers import EmailProvider
from lib.service import create_service_class

"""Email Services

This module defines all the actions possible with the email service. This service can be
safely used anywhere in the app.

Call these anywhere in the codebase by importing the service and running something like:

email.SendWelcomeEmail({"template": id, "email": "blabla@gmail.com", "data": (...)})

Pass a mock provider in testing with:
email.SendWelcomeEmail({...}, provider=MockProvider)

"""


Service = create_service_class(EmailProvider)


class SendWelcomeEmail(Service):
    template = forms.CharField()
    email = forms.EmailField()
    data = forms.MultiValueField()

    def action(self):
        self._provider.send_email(self.template, self.email)
