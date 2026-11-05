from dataclasses import dataclass
from decimal import Decimal

from auctions.models import Listing, ListingStateTransition, ListingStatus
from items.models import Item


@dataclass
class CreateListingPayload:
    item: Item
    starting_price: Decimal


def create_listing(payload: CreateListingPayload) -> Listing:
    listing = Listing.objects.create(
        item_id=payload.item.pk,
        starting_price=payload.starting_price
    )
    ListingStateTransition.objects.create(listing_id=listing.pk, status=ListingStatus.DRAFT.value)
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
    current_state = ListingStateTransition.objects.order_by("-created_at", "-id").only("status")
    next_state = lambda : ListingStateTransition.objects.create(listing_id=listing.pk, status=state.value)
    if not current_state or current_state not in list(ListingStatus):
        ListingStateTransition.objects.create(listing_id=listing.pk, status=ListingStatus.DRAFT.value)
        return listing

    if current_state in [ListingStatus.COMPLETE, ListingStatus.VOID]:
        raise RuntimeError("Cannot transition completed/ voided Listing.")

    if current_state == ListingStatus.DRAFT.value:
        if state in [ListingStatus.ACTIVE, ListingStatus.VOID, ListingStatus.INACTIVE]:
            next_state()
            return listing

    if current_state == ListingStatus.ACTIVE.value:
        if state in [ListingStatus.INACTIVE, ListingStatus.VOID, ListingStatus.COMPLETE]:
            next_state()
            return listing

    if current_state == ListingStatus.INACTIVE.value:
        if state in [ListingStatus.ACTIVE, ListingStatus.VOID, ListingStatus.COMPLETE]:
            next_state()
            return listing

    return listing

def pause_listing(listing: Listing) -> Listing:
    return _transition_listing_state(listing, ListingStatus.INACTIVE)

def void_listing(listing: Listing) -> Listing:
    return _transition_listing_state(listing, ListingStatus.VOID)

def complete_listing(listing: Listing) -> Listing:
    return _transition_listing_state(listing, ListingStatus.COMPLETE)

def activate_listing(listing: Listing) -> Listing:
    return _transition_listing_state(listing, ListingStatus.ACTIVE)
