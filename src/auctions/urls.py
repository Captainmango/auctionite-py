from django.urls import path
from . import views

urlpatterns = [
    path("listings", views.ListingBasicView.as_view(), name="listings.list"),
    path("listings", views.ListingBasicView.as_view(), name="listings.create"),
    path("listings/<int:listing_id>", views.ListingDetailsView.as_view(), name="listings.details"),
    path("listings/<int:listing_id>/bid", views.AuctionBidView.as_view(), name="listings.bid"),
]