import io

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from items.models import Item, ItemPictures

User = get_user_model()
payload = {
    "username": "test123",
    "email": "admin@admin.com",
    "password": "super-secure"
}

def make_image(name="pic.png", size=(10, 10), color="red"):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")

class CreateItemViewTest(APITestCase):
    def setUp(self) -> None:
        self.url = reverse("items.create")
        self.user = User.objects.create_user(**payload)

    def test_it_can_create_an_item(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post(self.url, {
            "name": "test",
            "description": "test desc",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Item.objects.filter(name="test").exists())

    def test_it_can_save_images(self):
        f = make_image("test.png")
        self.client.force_authenticate(user=self.user)
        res = self.client.post(self.url, {
            "name": "test",
            "description": "test desc",
            "pictures": [f]
        }, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        created_item = Item.objects.filter(name="test").first()
        self.assertIsNotNone(created_item)
        self.assertEqual(created_item.item_pictures.count(), 1)
