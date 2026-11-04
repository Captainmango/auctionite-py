from django.urls import path

from . import views

urlpatterns = [
    path("items", views.ItemView.as_view(), name="items.create"),
    path("items", views.ItemView.as_view(), name="items.list"),
    path("items/<int:item_id>", views.ItemDetailView.as_view(), name="items.update"),
    path("items/<int:item_id>", views.ItemDetailView.as_view(), name="items.delete"),
]
