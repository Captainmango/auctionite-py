from django.db.models.query import Prefetch
from rest_framework import status, response
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from auctions.models import Listing, ListingStateTransition
from auctions.serialisers import ListingDetailsSerialiser, ListingSerialiser, CreateListingRequest
from auctions.services import CreateListingPayload, create_listing
from items.models import Item

_paginator = LimitOffsetPagination()

class ListingController:
    def get_listings(self, request: Request) -> Response:
        listings = Listing.objects.filter(item__owner_id=request.user.pk)
        page = _paginator.paginate_queryset(listings, request)
        serialiser = ListingSerialiser(page, many=True)
        return _paginator.get_paginated_response(serialiser.data)

    def get_listing(self, request: Request, listing_id: int) -> Response:
        listing = Listing.objects.prefetch_related(
            Prefetch(
                "status",
                queryset=ListingStateTransition.objects.order_by("-id", "-created_at"),
                to_attr="status_changes"
            )
        ).filter(pk=listing_id, item__owner_id=request.user.pk).first()

        if not listing:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        return Response(ListingDetailsSerialiser(listing).data, status=status.HTTP_200_OK)

    def create_listing(self, request: Request) -> Response:
        serialiser = CreateListingRequest(data=request.data)
        serialiser.is_valid(raise_exception=True)
        item = get_object_or_404(Item, pk=serialiser.validated_data.get("item_id"))
        payload = CreateListingPayload(
            item = item,
            starting_price=serialiser.validated_data.get("starting_price")
        )
        listing = create_listing(payload)
        return Response(ListingSerialiser(instance=listing).data, status=status.HTTP_200_OK)
