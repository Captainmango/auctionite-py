from django.urls import path
from . import views

urlpatterns = [
    path("listings", views.ListingListView.as_view(), name="listings.list"),
    path("listings/<int:listing_id>", views.ListingDetailsView.as_view(), name="listings.details"),
]