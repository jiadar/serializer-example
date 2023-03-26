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
    link = forms.URLField()

    def action(self):
        return self.provider.send_email(
            self.cleaned_data["template"],
            self.cleaned_data["email"],
            {"link": self.cleaned_data["link"]},
        )
