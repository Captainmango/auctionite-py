from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from auctions.models import Listing, ListingStateTransition
from items.models import Item

payload = {
    "username": "test123",
    "email": "admin@admin.com",
    "password": "super-secure",
}

def create_dummy_listing(item: Item, price: Decimal) -> Listing:
    listing = Listing.objects.create(starting_price=price, item_id=item.pk)
    ListingStateTransition.objects.create(listing_id=listing.pk)
    return listing


class ListingDetailsViewTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(**payload)
        self.item = Item.objects.create(
            name="Test Item 1",
            description="Test Item Description",
            owner_id=self.user.id,
        )
        self.listing = create_dummy_listing(item=self.item, price=Decimal(25.00))
        self.url = reverse("listings.details", kwargs={"listing_id": self.listing.pk})

    def test_it_can_view_the_listing(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        json_data = res.json().get("data", {})
        self.assertEqual(json_data.get("id"), self.listing.pk)

    def test_it_protects_listings_with_items_not_owned(self):
        other_user_payload = payload.copy()
        other_user_payload["username"] = "another-user"
        other_user_payload["email"] = "another-user@admin.com"
        other_user = User.objects.create(**other_user_payload)

        self.client.force_authenticate(other_user)

        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class ListingListViewTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(**payload)
        item1 = Item.objects.create(
            name="Test Item 1",
            description="Test Item Description",
            owner_id=self.user.id,
        )
        item2 = Item.objects.create(
            name="Test Item 1",
            description="Test Item Description",
            owner_id=self.user.id,
        )
        create_dummy_listing(item=item1, price=Decimal(25.00))
        create_dummy_listing(item=item2, price=Decimal(10.00))
        self.url = reverse("listings.list")

    def test_it_can_view_the_listings(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        data = res.json().get("data", {})
        print(data)
