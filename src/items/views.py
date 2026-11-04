from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsOwner
from items.controllers import ItemController

_item_controller = ItemController()


class ItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        return _item_controller.create_item(request)

    def get(self, request: Request) -> Response:
        return _item_controller.get_items(request)


class ItemDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def patch(self, request: Request, item_id: int) -> Response:
        return _item_controller.update_item(request, item_id)

    def delete(self, request: Request, item_id: int) -> Response:
        return _item_controller.delete_item(request, item_id)
