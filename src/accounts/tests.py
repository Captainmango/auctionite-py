from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class RegisterViewTest(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("users.register")
        self.payload = {
            "username": "test123",
            "email": "admin@admin.com",
            "password": "super-secure"
        }

    def test_it_can_register_when_details_are_correct(self):
        res = self.client.post(self.url, self.payload, format="json")
        self.assertIs(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.json(), {"data": {"id": 1}})

    def test_it_rejects_duplicate_username(self):
        User.objects.create_user(**self.payload)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_it_rejects_missing_fields(self):
        for field in self.payload:
            with self.subTest(missing=field):
                data = {k: v for k, v in self.payload.items() if k != field}
                res = self.client.post(self.url, data, format="json")
                self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
                self.assertIn(field, res.json())