from typing import cast

from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from auctions.errors import (
    AlreadyLeadingAuction,
    BidBehindCurrentLeader,
    BidBelowStartingPrice,
    CannotBidOnOwnListing,
)
from auctions.models import Listing
from auctions.serialisers import (
    BidAmountSerialiser,
    CreateListingRequest,
    ListingDetailsSerialiser,
    ListingSerialiser,
)
from auctions.services import (
    CreateListingPayload,
    ListingManagementProtocol,
    ListingService,
)
from items.models import Item

_paginator = LimitOffsetPagination()


class ListingController:
    def __init__(self, listing_service: ListingManagementProtocol | None = None):
        self._listing_service = listing_service or ListingService()

    def get_listings(self, request: Request) -> Response:
        listings = self._listing_service.user_listings(cast(int, request.user.pk))
        page = _paginator.paginate_queryset(listings, request)
        serialiser = ListingSerialiser(page, many=True)
        return _paginator.get_paginated_response(serialiser.data)

    def get_listing(self, request: Request, listing_id: int) -> Response:
        listing = self._listing_service.owned_listing_with_status(
            listing_id, cast(int, request.user.pk)
        )
        if not listing:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            ListingDetailsSerialiser(listing).data, status=status.HTTP_200_OK
        )

    def create_listing(self, request: Request) -> Response:
        serialiser = CreateListingRequest(data=request.data)
        serialiser.is_valid(raise_exception=True)
        item = get_object_or_404(Item, pk=serialiser.validated_data.get("item_id"))
        payload = CreateListingPayload(
            item=item, starting_price=serialiser.validated_data.get("starting_price")
        )
        listing = self._listing_service.create(payload)
        return Response(
            ListingSerialiser(instance=listing).data, status=status.HTTP_200_OK
        )

    def place_bid(self, request: Request, listing_id: int) -> Response:
        serialiser = BidAmountSerialiser(data=request.data)
        serialiser.is_valid(raise_exception=True)
        listing = get_object_or_404(Listing, pk=listing_id)
        user_id: int = cast(int, request.user.pk)
        try:
            self._listing_service.place_bid(
                user_id, listing, serialiser.validated_data.get("amount")
            )
        except CannotBidOnOwnListing as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        except AlreadyLeadingAuction as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        except BidBehindCurrentLeader as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except BidBelowStartingPrice as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        return Response({}, status=status.HTTP_200_OK)
