import io

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from items.models import Item, ItemPictures
from items.serialisers import ItemSerialiser, ItemPicturesSerialiser, CreateItemRequest


class ItemController:
    def __init__(
            self,
            item_serialiser = None,
            item_picture_serialiser = None,
            item_create_serialiser = None
    ):
        self._item_serialiser = item_serialiser or ItemSerialiser
        self._item_picture_serialiser = item_picture_serialiser or ItemPicturesSerialiser
        self._item_create_serialiser = item_create_serialiser or CreateItemRequest

    def create_item(self, request: Request) -> Response:
        serialiser = self._item_create_serialiser(data=request.data)
        serialiser.is_valid(raise_exception=True)
        item = Item.objects.create(
            name=serialiser.data.get("name"),
            description=serialiser.data.get("description"),
            owner_id=request.user.id,
        )
        pictures_to_upload = [ItemPictures(blob=b.read(), item_id=item.id)
                              for b in serialiser.validated_data.get("pictures", [])]
        item.item_pictures.bulk_create(pictures_to_upload)

        return Response(serialiser.data, status=status.HTTP_201_CREATED)