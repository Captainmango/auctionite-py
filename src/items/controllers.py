from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from items.models import Item, ItemPictures
from items.serialisers import CreateItemRequest, ItemPicturesSerialiser, ItemSerialiser

_paginator = LimitOffsetPagination()


class ItemController:
    def __init__(
        self,
        item_serialiser=None,
        item_picture_serialiser=None,
        item_create_serialiser=None,
    ):
        self._item_serialiser = item_serialiser or ItemSerialiser
        self._item_picture_serialiser = (
            item_picture_serialiser or ItemPicturesSerialiser
        )
        self._item_create_serialiser = item_create_serialiser or CreateItemRequest

    def create_item(self, request: Request) -> Response:
        serialiser = self._item_create_serialiser(data=request.data)
        serialiser.is_valid(raise_exception=True)
        item = Item.objects.create(
            name=serialiser.data.get("name"),
            description=serialiser.data.get("description"),
            owner_id=request.user.id,
        )
        pictures_to_upload = [
            ItemPictures(blob=b.read(), item_id=item.id)
            for b in serialiser.validated_data.get("pictures", [])
        ]
        item.item_pictures.bulk_create(pictures_to_upload)

        return Response(serialiser.data, status=status.HTTP_201_CREATED)

    def update_item(self, request: Request, item_id: int) -> Response:
        item = get_object_or_404(Item, pk=item_id)
        listing = getattr(item, "listing", None)
        if listing is not None and not listing.can_be_edited:
            return Response({}, status=status.HTTP_409_CONFLICT)

        serialiser = self._item_create_serialiser(data=request.data)
        serialiser.is_valid(raise_exception=True)
        to_update = {k: serialiser.data[k] for k in ["name", "description"]}
        Item.objects.filter(id=item_id).update(**to_update)
        item.refresh_from_db()
        return Response(
            self._item_serialiser(instance=item).data, status=status.HTTP_200_OK
        )

    def delete_item(self, _request: Request, item_id: int) -> Response:
        rows_del, _ = Item.objects.filter(id=item_id).delete()
        if rows_del == 0:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        return Response({}, status=status.HTTP_200_OK)

    def get_items(self, request: Request) -> Response:
        items = Item.objects.filter(owner_id=request.user.id)
        page = _paginator.paginate_queryset(items, request)
        serialiser = self._item_serialiser(instance=page, many=True)
        return _paginator.get_paginated_response(serialiser.data)
