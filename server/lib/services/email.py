from django import forms
from lib.providers import EmailProvider
from lib.service import create_service_class

"""Email Services

This module defines all the actions possible with the email service. This service can be
safely used anywhere in the app.
"""


Service = create_service_class(EmailProvider)


class Send(Service):
    template = forms.CharField()
    email = forms.EmailField()

    def action(self):
        self._provider.send_email(self.template, self.email)
