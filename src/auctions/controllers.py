from typing import cast

from django.db.models.query import Prefetch
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from auctions.models import Listing, ListingStateTransition
from auctions.serialisers import (
    BidAmountSerialiser,
    CreateListingRequest,
    ListingDetailsSerialiser,
    ListingSerialiser,
)
from auctions.services import (
    AlreadyLeadingAuction,
    BidBehindCurrentLeader,
    BidBelowStartingPrice,
    CannotBidOnOwnListing,
    CreateListingPayload,
    create_listing,
    place_bid_for,
)
from items.models import Item

_paginator = LimitOffsetPagination()


class ListingController:
    def get_listings(self, request: Request) -> Response:
        listings = Listing.objects.filter(item__owner_id=request.user.pk)
        page = _paginator.paginate_queryset(listings, request)
        serialiser = ListingSerialiser(page, many=True)
        return _paginator.get_paginated_response(serialiser.data)

    def get_listing(self, request: Request, listing_id: int) -> Response:
        listing = (
            Listing.objects.prefetch_related(
                Prefetch(
                    "status",
                    queryset=ListingStateTransition.objects.order_by(
                        "-id", "-created_at"
                    ),
                    to_attr="status_changes",
                )
            )
            .filter(pk=listing_id, item__owner_id=request.user.pk)
            .first()
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
        listing = create_listing(payload)
        return Response(
            ListingSerialiser(instance=listing).data, status=status.HTTP_200_OK
        )

    def place_bid(self, request: Request, listing_id: int) -> Response:
        serialiser = BidAmountSerialiser(data=request.data)
        serialiser.is_valid(raise_exception=True)
        listing = get_object_or_404(Listing, pk=listing_id)
        user_id: int = cast(int, request.user.pk)
        try:
            place_bid_for(user_id, listing, serialiser.validated_data.get("amount"))
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
