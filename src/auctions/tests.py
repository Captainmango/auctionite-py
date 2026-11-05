from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from auctions.models import Listing, ListingStateTransition, ListingStatus
from auctions.services import (
    CreateListingPayload,
    _transition_listing_state,
    activate_listing,
    complete_listing,
    create_listing,
    pause_listing,
    void_listing,
)
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


class ListingBasicViewTest(APITestCase):
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
        self.assertEqual(data.get("count"), 2)

    def test_it_creates_a_listing(self):
        self.client.force_authenticate(self.user)
        another_item = Item.objects.create(
            name="Test Item 1",
            description="Test Item Description",
            owner_id=self.user.id,
        )
        res = self.client.post(reverse("listings.create"), {
            "item_id": another_item.pk,
            "starting_price": 23.99
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json().get("data")
        listing = Listing.objects.filter(pk=data.get("id")).first()
        assert listing is not None


class ListingStateMachineTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(**payload)
        self.item = Item.objects.create(
            name="State Machine Item",
            description="Test Item Description",
            owner_id=self.user.id,
        )
        self.listing = Listing.objects.create(
            item_id=self.item.pk, starting_price=Decimal("25.00")
        )

    def _set_state(self, state: ListingStatus):
        ListingStateTransition.objects.create(
            listing_id=self.listing.pk, status=state.value
        )

    def _latest_status(self) -> str:
        latest = self.listing.status.order_by("-created_at", "-id").first()
        assert latest is not None
        return latest.status

    def _transition_count(self) -> int:
        return ListingStateTransition.objects.filter(listing_id=self.listing.pk).count()

    def test_create_listing_starts_in_draft(self):
        fresh_item = Item.objects.create(
            name="Fresh Item",
            description="Test Item Description",
            owner_id=self.user.id,
        )
        listing = create_listing(
            CreateListingPayload(item=fresh_item, starting_price=Decimal("10.00"))
        )
        latest = listing.status.order_by("-created_at", "-id").first()
        assert latest is not None
        self.assertEqual(latest.status, ListingStatus.DRAFT.value)

    def test_stateless_listing_any_transition_sets_draft_and_returns_early(self):
        activate_listing(self.listing)
        self.assertEqual(self._latest_status(), ListingStatus.DRAFT.value)
        self.assertEqual(self._transition_count(), 1)

    def test_draft_can_transition_to_active_inactive_or_void(self):
        for state, action in [
            (ListingStatus.ACTIVE, activate_listing),
            (ListingStatus.INACTIVE, pause_listing),
            (ListingStatus.VOID, void_listing),
        ]:
            with self.subTest(target=state.value):
                ListingStateTransition.objects.filter(listing_id=self.listing.pk).delete()
                self._set_state(ListingStatus.DRAFT)
                action(self.listing)
                self.assertEqual(self._latest_status(), state.value)

    def test_draft_cannot_transition_to_complete(self):
        self._set_state(ListingStatus.DRAFT)
        with self.assertRaises(RuntimeError):
            complete_listing(self.listing)
        self.assertEqual(self._latest_status(), ListingStatus.DRAFT.value)

    def test_draft_cannot_transition_to_draft(self):
        self._set_state(ListingStatus.DRAFT)
        with self.assertRaises(RuntimeError):
            _transition_listing_state(self.listing, ListingStatus.DRAFT)
        self.assertEqual(self._transition_count(), 1)

    def test_active_can_transition_to_inactive_void_or_complete(self):
        for state, action in [
            (ListingStatus.INACTIVE, pause_listing),
            (ListingStatus.VOID, void_listing),
            (ListingStatus.COMPLETE, complete_listing),
        ]:
            with self.subTest(target=state.value):
                ListingStateTransition.objects.filter(listing_id=self.listing.pk).delete()
                self._set_state(ListingStatus.ACTIVE)
                action(self.listing)
                self.assertEqual(self._latest_status(), state.value)

    def test_active_cannot_transition_to_active(self):
        self._set_state(ListingStatus.ACTIVE)
        with self.assertRaises(RuntimeError):
            activate_listing(self.listing)
        self.assertEqual(self._latest_status(), ListingStatus.ACTIVE.value)

    def test_inactive_can_transition_to_active_void_or_complete(self):
        for state, action in [
            (ListingStatus.ACTIVE, activate_listing),
            (ListingStatus.VOID, void_listing),
            (ListingStatus.COMPLETE, complete_listing),
        ]:
            with self.subTest(target=state.value):
                ListingStateTransition.objects.filter(listing_id=self.listing.pk).delete()
                self._set_state(ListingStatus.INACTIVE)
                action(self.listing)
                self.assertEqual(self._latest_status(), state.value)

    def test_inactive_cannot_transition_to_inactive(self):
        self._set_state(ListingStatus.INACTIVE)
        with self.assertRaises(RuntimeError):
            pause_listing(self.listing)
        self.assertEqual(self._latest_status(), ListingStatus.INACTIVE.value)

    def test_void_is_terminal(self):
        self._set_state(ListingStatus.VOID)
        for action in [activate_listing, pause_listing, complete_listing, void_listing]:
            with self.subTest(action=action.__name__):
                with self.assertRaises(RuntimeError):
                    action(self.listing)
        self.assertEqual(self._latest_status(), ListingStatus.VOID.value)
        self.assertEqual(self._transition_count(), 1)

    def test_complete_is_terminal(self):
        self._set_state(ListingStatus.COMPLETE)
        for action in [activate_listing, pause_listing, complete_listing, void_listing]:
            with self.subTest(action=action.__name__):
                with self.assertRaises(RuntimeError):
                    action(self.listing)
        self.assertEqual(self._latest_status(), ListingStatus.COMPLETE.value)
        self.assertEqual(self._transition_count(), 1)

    def test_successful_transitions_append_history(self):
        self._set_state(ListingStatus.DRAFT)
        activate_listing(self.listing)
        pause_listing(self.listing)
        complete_listing(self.listing)
        history = list(
            self.listing.status.order_by("created_at", "id").values_list(
                "status", flat=True
            )
        )
        self.assertEqual(
            history,
            [
                ListingStatus.DRAFT.value,
                ListingStatus.ACTIVE.value,
                ListingStatus.INACTIVE.value,
                ListingStatus.COMPLETE.value,
            ],
        )

    def test_failed_transition_writes_no_history(self):
        self._set_state(ListingStatus.DRAFT)
        with self.assertRaises(RuntimeError):
            complete_listing(self.listing)
        self.assertEqual(self._transition_count(), 1)

    def test_can_be_edited_by_state(self):
        for state, editable in [
            (ListingStatus.DRAFT, True),
            (ListingStatus.INACTIVE, True),
            (ListingStatus.ACTIVE, False),
            (ListingStatus.VOID, False),
            (ListingStatus.COMPLETE, False),
        ]:
            with self.subTest(state=state.value):
                ListingStateTransition.objects.filter(listing_id=self.listing.pk).delete()
                self._set_state(state)
                self.assertEqual(self.listing.can_be_edited, editable)

    def test_can_be_edited_with_no_state(self):
        self.assertTrue(self.listing.can_be_edited)
