from typing import cast

from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from items.models import Item
from items.serialisers import UpsertItemRequest, ItemSerialiser
from items.services import ItemManagementProtocol, ItemService, CreateItemPayload, UpdateItemPayload

_paginator = LimitOffsetPagination()


class ItemController:
    def __init__(
            self,
            item_service: ItemManagementProtocol | None = None
    ):
        self._item_service = item_service or ItemService()

    def create_item(self, request: Request) -> Response:
        serialiser = UpsertItemRequest(data=request.data)
        serialiser.is_valid(raise_exception=True)
        payload = CreateItemPayload.from_dict(serialiser.validated_data)
        user_id = cast(int, request.user.pk)
        self._item_service.create(user_id, payload)
        return Response(serialiser.data, status=status.HTTP_201_CREATED)

    def update_item(self, request: Request, item_id: int) -> Response:
        item = get_object_or_404(Item, pk=item_id)
        serialiser = UpsertItemRequest(data=request.data)
        serialiser.is_valid(raise_exception=True)
        to_update = UpdateItemPayload(**{k: serialiser.data[k] for k in ["name", "description"]})
        item = self._item_service.update(item, payload=to_update)
        return Response(
            ItemSerialiser(instance=item).data, status=status.HTTP_200_OK
        )

    def delete_item(self, _request: Request, item_id: int) -> Response:
        is_deleted = self._item_service.delete(item_id)
        if not is_deleted:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        return Response({}, status=status.HTTP_200_OK)

    def get_items(self, request: Request) -> Response:
        items = self._item_service.user_items_queryset(cast(int,request.user.pk))
        page = _paginator.paginate_queryset(items, request)
        serialiser = ItemSerialiser(instance=page, many=True)
        return _paginator.get_paginated_response(serialiser.data)
