from dataclasses import dataclass, asdict, field
from typing import runtime_checkable, Protocol, Any, cast

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import QuerySet

from auctions.models import Listing
from items.errors import CannotEditItem
from items.models import Item, ItemPictures


@dataclass
class CreateItemPayload:
    name: str
    description: str
    pictures: list[UploadedFile] | None = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CreateItemPayload":
        return cls(**d)


@dataclass
class UpdateItemPayload:
    name: str
    description: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "UpdateItemPayload":
        return cls(**d)


@runtime_checkable
class ItemManagementProtocol(Protocol):
    def create(self, user_id: int, payload: CreateItemPayload) -> Item:
        ...
    def save_pictures(self, item: Item, pictures: list[UploadedFile]):
        ...
    def update(self, item: Item, payload: UpdateItemPayload) -> Item:
        ...
    def delete(self, item_id: int) -> bool:
        ...
    def user_items_queryset(self, user_id: int) -> QuerySet:
        ...


class ItemService(ItemManagementProtocol):
    def create(self, user_id: int, payload: CreateItemPayload) -> Item:
        with transaction.atomic():
            item = Item.objects.create(
                name=payload.name,
                description=payload.description,
                owner_id=user_id,
            )
            if payload.pictures is not None:
                self.save_pictures(item, payload.pictures)
            return item

    def save_pictures(self, item: Item, pictures: list[UploadedFile]):
        pictures_to_upload = [
            ItemPictures(blob=b.read(), item_id=item.id)
            for b in pictures
        ]
        item.item_pictures.bulk_create(pictures_to_upload)

    def update(self, item: Item, payload: UpdateItemPayload) -> Item:
        listing: Listing | None = getattr(item, "listing", None)
        if listing is not None and not listing.can_be_edited:
            raise CannotEditItem()
        Item.objects.filter(id=item.pk).update(**asdict(payload))
        item.refresh_from_db()
        return item

    def delete(self, item_id: int) -> bool:
        rows_del, _ = Item.objects.filter(id=item_id).delete()
        return rows_del != 0

    def user_items_queryset(self, user_id: int) -> QuerySet:
        return Item.objects.filter(owner_id=user_id)
