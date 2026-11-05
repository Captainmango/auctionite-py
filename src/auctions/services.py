from dataclasses import dataclass
from decimal import Decimal

from auctions.errors import (
    AlreadyLeadingAuction,
    BidBehindCurrentLeader,
    BidBelowStartingPrice,
    CannotBidOnOwnListing,
)
from auctions.models import Bid, Listing, ListingStateTransition, ListingStatus
from common.helpers import synchronise
from items.models import Item


@dataclass
class CreateListingPayload:
    item: Item
    starting_price: Decimal


def create_listing(payload: CreateListingPayload) -> Listing:
    listing = Listing.objects.create(
        item_id=payload.item.pk, starting_price=payload.starting_price
    )
    ListingStateTransition.objects.create(
        listing_id=listing.pk, status=ListingStatus.DRAFT.value
    )
    return listing


def _transition_listing_state(listing: Listing, state: ListingStatus) -> Listing:
    """
    Listing state transition state machine. If no state, sets the state to draft and returns early.

    State transitions are as follows:
    - Created Listings all start in Draft status
    - Draft can transition to Active, Inactive, or Void
    - Active can transition to Inactive, Void, or Complete
    - Inactive can transition to Active, Void, or Complete
    - Void and Complete cannot transition. They are terminal.
    """
    current_state: ListingStateTransition | None = (
        ListingStateTransition.objects.filter(listing_id=listing.id)
        .order_by("-created_at", "-id")
        .only("status")
        .first()
    )

    def next_state():
        ListingStateTransition.objects.create(listing_id=listing.pk, status=state.value)

    if not current_state or current_state.status not in list(ListingStatus):
        ListingStateTransition.objects.create(
            listing_id=listing.pk, status=ListingStatus.DRAFT.value
        )
        return listing

    if current_state.status in [ListingStatus.COMPLETE, ListingStatus.VOID]:
        raise RuntimeError("Cannot transition completed/ voided Listing.")

    if current_state.status == ListingStatus.DRAFT.value:
        if state in [ListingStatus.ACTIVE, ListingStatus.VOID, ListingStatus.INACTIVE]:
            next_state()
            return listing
        else:
            raise RuntimeError("Invalid transition")

    if current_state.status == ListingStatus.ACTIVE.value:
        if state in [
            ListingStatus.INACTIVE,
            ListingStatus.VOID,
            ListingStatus.COMPLETE,
        ]:
            next_state()
            return listing
        else:
            raise RuntimeError("Invalid transition")

    if current_state.status == ListingStatus.INACTIVE.value:
        if state in [ListingStatus.ACTIVE, ListingStatus.VOID, ListingStatus.COMPLETE]:
            next_state()
            return listing
        else:
            raise RuntimeError("Invalid transition")

    return listing


def pause_listing(listing: Listing) -> Listing:
    return _transition_listing_state(listing, ListingStatus.INACTIVE)


def void_listing(listing: Listing) -> Listing:
    return _transition_listing_state(listing, ListingStatus.VOID)


def complete_listing(listing: Listing) -> Listing:
    return _transition_listing_state(listing, ListingStatus.COMPLETE)


def activate_listing(listing: Listing) -> Listing:
    return _transition_listing_state(listing, ListingStatus.ACTIVE)


def place_bid_for(user_id: int, listing: Listing, bid_amount: Decimal):
    def bid_helper(ui: int, li: Listing, ba: Decimal):
        if li.item.owner_id == ui:
            raise CannotBidOnOwnListing()
        current_leader: Bid | None = (
            Bid.objects.filter(listing_id=li.pk)
            .order_by("-amount", "created_at")
            .first()
        )
        if current_leader is None:
            if ba <= li.starting_price:
                raise BidBelowStartingPrice()
            Bid.objects.create(listing_id=li.pk, user_id=ui, amount=ba)
            return
        if current_leader.user_id == ui:
            raise AlreadyLeadingAuction
        if current_leader.amount >= ba:
            raise BidBehindCurrentLeader()
        Bid.objects.create(listing_id=li.pk, user_id=ui, amount=ba)

    try:
        synchronise(
            key=f"{listing.pk}-{user_id}",
            ttl_seconds=10,
            retries=5,
            timeout_seconds=10,
            callback=bid_helper,
            ui=user_id,
            li=listing,
            ba=bid_amount,
        )
    except RuntimeError as e:
        raise e
