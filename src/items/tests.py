import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from items.models import Item

payload = {
    "username": "test123",
    "email": "admin@admin.com",
    "password": "super-secure",
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
        res = self.client.post(
            self.url,
            {
                "name": "test",
                "description": "test desc",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Item.objects.filter(name="test").exists())

    def test_it_can_save_images(self):
        f = make_image("test.png")
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            self.url,
            {"name": "test", "description": "test desc", "pictures": [f]},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        created_item = Item.objects.filter(name="test").first()
        self.assertIsNotNone(created_item)
        self.assertEqual(created_item.item_pictures.count(), 1)


class UpdateItemViewTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(**payload)
        self.item = Item.objects.create(
            name="Test Item 1",
            description="Test Item Description",
            owner_id=self.user.id,
        )
        self.url = reverse("items.update", kwargs={"item_id": self.item.id})

    def test_it_can_update_an_item(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(
            self.url,
            {
                "name": "test",
                "description": "test desc",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(Item.objects.filter(name="test").exists())


class DeleteItemViewTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(**payload)
        self.item = Item.objects.create(
            name="Test Item 1",
            description="Test Item Description",
            owner_id=self.user.id,
        )
        self.url = reverse("items.delete", kwargs={"item_id": self.item.id})

    def test_it_can_delete_an_item(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.delete(self.url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(Item.objects.filter(name="test").exists())


class ListItemViewTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(**payload)
        self.item = Item.objects.create(
            name="Test Item 1",
            description="Test Item Description",
            owner_id=self.user.id,
        )
        self.item = Item.objects.create(
            name="Test Item 2",
            description="Test Item Description",
            owner_id=self.user.id,
        )
        self.url = reverse("items.list")

    def test_it_lists_owner_items(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json().get("data", {}).get("results")), 2)

    def test_it_allows_custom_pages(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.url, query_params={"limit": 1})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        result_data = res.json().get("data", {})
        self.assertEqual(len(result_data.get("results")), 1)
        self.assertIn("offset=1", result_data.get("next"))
