from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from auctions.controllers import ListingController


_listing_controller = ListingController()


class ListingBasicView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        return _listing_controller.get_listings(request)

    def post(self, request: Request) -> Response:
        return _listing_controller.create_listing(request)


class ListingDetailsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, listing_id: int) -> Response:
        return _listing_controller.get_listing(request, listing_id)
