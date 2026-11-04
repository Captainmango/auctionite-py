from django.shortcuts import render
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from items.controllers import ItemController

_item_controller = ItemController()

class CreateItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        return _item_controller.create_item(request)

