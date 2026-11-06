from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable

from django.db import transaction
from django.db.models import QuerySet
from django.db.models.query import Prefetch

from auctions.errors import (
    AlreadyLeadingAuction,
    BidBehindCurrentLeader,
    BidBelowStartingPrice,
    CannotBidOnOwnListing,
)
from auctions.models import Bid, Listing, ListingStateTransition, ListingStatus
from common.helpers import synchronise
from items.models import Item

_TRANSITIONS: dict[str, list[ListingStatus]] = {
    ListingStatus.DRAFT.value: [
        ListingStatus.ACTIVE,
        ListingStatus.INACTIVE,
        ListingStatus.VOID,
    ],
    ListingStatus.ACTIVE.value: [
        ListingStatus.INACTIVE,
        ListingStatus.VOID,
        ListingStatus.COMPLETE,
    ],
    ListingStatus.INACTIVE.value: [
        ListingStatus.ACTIVE,
        ListingStatus.VOID,
        ListingStatus.COMPLETE,
    ],
}


@dataclass
class CreateListingPayload:
    item: Item
    starting_price: Decimal


@runtime_checkable
class ListingManagementProtocol(Protocol):
    def create(self, payload: CreateListingPayload) -> Listing: ...
    def transition_state(self, listing: Listing, state: ListingStatus) -> Listing: ...
    def activate(self, listing: Listing) -> Listing: ...
    def pause(self, listing: Listing) -> Listing: ...
    def void(self, listing: Listing) -> Listing: ...
    def complete(self, listing: Listing) -> Listing: ...
    def place_bid(self, user_id: int, listing: Listing, bid_amount: Decimal) -> Bid: ...
    def user_listings(self, user_id: int) -> QuerySet: ...
    def owned_listing_with_status(self, listing_id: int, user_id: int) -> Listing | None: ...


class ListingService(ListingManagementProtocol):
    def create(self, payload: CreateListingPayload) -> Listing:
        with transaction.atomic():
            listing = Listing.objects.create(
                item_id=payload.item.pk, starting_price=payload.starting_price
            )
            ListingStateTransition.objects.create(
                listing_id=listing.pk, status=ListingStatus.DRAFT.value
            )
            return listing

    def transition_state(self, listing: Listing, state: ListingStatus) -> Listing:
        """
        Listing state transition state machine. If no state, sets the state to draft and returns early.

        State transitions are as follows:
        - Created Listings all start in Draft status
        - Draft can transition to Active, Inactive, or Void
        - Active can transition to Inactive, Void, or Complete
        - Inactive can transition to Active, Void, or Complete
        - Void and Complete cannot transition. They are terminal.
        """
        with transaction.atomic():
            # Lock the listing so concurrent transitions are applied in turn.
            Listing.objects.select_for_update().get(pk=listing.pk)
            current_state: ListingStateTransition | None = (
                ListingStateTransition.objects.filter(listing_id=listing.pk)
                .order_by("-created_at", "-id")
                .only("status")
                .first()
            )

            if not current_state or current_state.status not in list(ListingStatus):
                ListingStateTransition.objects.create(
                    listing_id=listing.pk, status=ListingStatus.DRAFT.value
                )
                return listing

            if current_state.status in [ListingStatus.COMPLETE, ListingStatus.VOID]:
                raise RuntimeError("Cannot transition completed/ voided Listing.")

            if state not in _TRANSITIONS.get(current_state.status, []):
                raise RuntimeError("Invalid transition")

            ListingStateTransition.objects.create(
                listing_id=listing.pk, status=state.value
            )
            return listing

    def activate(self, listing: Listing) -> Listing:
        return self.transition_state(listing, ListingStatus.ACTIVE)

    def pause(self, listing: Listing) -> Listing:
        return self.transition_state(listing, ListingStatus.INACTIVE)

    def void(self, listing: Listing) -> Listing:
        return self.transition_state(listing, ListingStatus.VOID)

    def complete(self, listing: Listing) -> Listing:
        return self.transition_state(listing, ListingStatus.COMPLETE)

    def place_bid(self, user_id: int, listing: Listing, bid_amount: Decimal) -> Bid:
        def bid_helper() -> Bid:
            with transaction.atomic():
                # Lock the listing so the leader is read and replaced atomically.
                Listing.objects.select_for_update().get(pk=listing.pk)
                if listing.item.owner_id == user_id:
                    raise CannotBidOnOwnListing()
                current_leader: Bid | None = (
                    Bid.objects.filter(listing_id=listing.pk)
                    .order_by("-amount", "created_at")
                    .first()
                )
                if current_leader is None:
                    if bid_amount <= listing.starting_price:
                        raise BidBelowStartingPrice()
                elif current_leader.user_id == user_id:
                    raise AlreadyLeadingAuction()
                elif current_leader.amount >= bid_amount:
                    raise BidBehindCurrentLeader()
                return Bid.objects.create(
                    listing_id=listing.pk, user_id=user_id, amount=bid_amount
                )

        return synchronise(
            key=f"{listing.pk}-{user_id}",
            ttl_seconds=10,
            retries=5,
            timeout_seconds=10,
            callback=bid_helper,
        )

    def user_listings(self, user_id: int) -> QuerySet:
        return Listing.objects.filter(item__owner_id=user_id)

    def owned_listing_with_status(self, listing_id: int, user_id: int) -> Listing | None:
        return (
            Listing.objects.prefetch_related(
                Prefetch(
                    "status",
                    queryset=ListingStateTransition.objects.order_by(
                        "-created_at", "id"
                    ),
                    to_attr="status_changes",
                )
            )
            .filter(pk=listing_id, item__owner_id=user_id)
            .first()
        )
