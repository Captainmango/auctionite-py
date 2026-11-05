from enum import StrEnum

from django.db import models

from common.models import BaseModel
from items.models import Item


class ListingStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    VOID = "VOID"
    COMPLETE = "COMPLETE"

    @classmethod
    def as_dict(cls) -> dict[str, str]:
        return {m.name: m.value for m in cls}

    @classmethod
    def editable_states(cls) -> list[str]:
        return [cls.INACTIVE, cls.DRAFT]

class Listing(BaseModel):
    item = models.OneToOneField(
        Item, on_delete=models.DO_NOTHING, blank=False, null=False
    )
    starting_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "listings"
        indexes = [models.Index(fields=["item_id"])]

    @property
    def can_be_edited(self) -> bool:
        latest = self.status.order_by("-created_at", "-id").only("status").first()
        if latest is None:
            return True
        return ListingStatus(latest.status) in ListingStatus.editable_states()


class ListingSchedule(BaseModel):
    listing = models.ForeignKey(Listing, on_delete=models.DO_NOTHING, related_name="scheduled_times")
    activates_at = models.DateTimeField(blank=False, null=True)
    deactivates_at = models.DateTimeField(blank=False, null=True)

    class Meta:
        db_table = "listing_schedules"
        indexes = [
            models.Index(fields=["listing_id"]),
            models.Index(fields=["activates_at"]),
            models.Index(fields=["deactivates_at"]),
        ]


class ListingStateTransition(BaseModel):
    listing = models.ForeignKey(Listing, on_delete=models.DO_NOTHING, related_name="status")
    status = models.CharField(
        choices=ListingStatus.as_dict(),
        default=ListingStatus.DRAFT,
    )

    class Meta:
        db_table = "listing_status_transitions"
        indexes = [models.Index(fields=["listing_id", "-created_at"])]


class Bid(BaseModel):
    listing = models.ForeignKey(
        Listing, on_delete=models.DO_NOTHING, related_name="bids"
    )
    user = models.ForeignKey(Listing, on_delete=models.DO_NOTHING)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "bids"
        indexes = [
            models.Index(fields=["listing_id"]),
            models.Index(fields=["user_id"]),
            models.Index(
                fields=["listing_id", "-amount", "created_at"],
                name="idx_bids_listing_leading",
            ),
        ]
