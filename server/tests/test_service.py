from django.test import TestCase
from lib.providers import MockEmailProvider
from lib.services import email


class EmailTestCase(TestCase):
    def test_email_service(self):
        instance = email.SendWelcomeEmail(
            {
                "template": "4jfdginx235sdfg",
                "email": "jiadar@gmail.com",
                "link": "https://usekilo.com/activate/439tj93jgsidfjg9qjgf",
            },
            provider=MockEmailProvider,
        )
        self.assertEqual(instance.result, {"status": "ok"})
