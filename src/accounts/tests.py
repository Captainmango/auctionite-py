from django.test import TestCase


class RegisterViewTest(TestCase):
    def test_it_can_register(self):
        res = self.client.post("api/v1/auth/register", data={
            "username": "test123",
            "email": "admin@admin.com",
            "password": "super-secure"
        })
        self.assertIs(res, "ww")
