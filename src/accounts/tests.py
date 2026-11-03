from django.test import TestCase
from rest_framework import status


class RegisterViewTest(TestCase):
    def test_it_can_register_when_details_are_correct(self):
        res = self.client.post("/api/v1/auth/register", data={
            "username": "test123",
            "email": "admin@admin.com",
            "password": "super-secure"
        })
        self.assertIs(res.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(res.content, "{\"id\": 1}")

    def test_it_validates_password_is_required(self):
        res = self.client.post("/api/v1/auth/register", data={
            "username": "test123",
            "email": "admin@admin.com",
        })
        self.assertIs(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.content, b'{"password":["This field is required."]}')

    def test_it_validates_email_is_required(self):
        res = self.client.post("/api/v1/auth/register", data={
            "username": "test123",
            "password": "super-secure"
        })
        self.assertIs(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.content, b'{"email":["This field is required."]}')

    def test_it_validates_username_is_required(self):
        res = self.client.post("/api/v1/auth/register", data={
            "email": "admin@admin.com",
            "password": "super-secure"
        })
        self.assertIs(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.content, b'{"username":["This field is required."]}')

    def test_it_validates_password_is_correct_length(self):
        res = self.client.post("/api/v1/auth/register", data={
            "username": "test123",
            "email": "admin@admin.com",
            "password": "super"
        })
        self.assertIs(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.content, b'{"password":["Ensure this field has at least 6 characters."]}')
