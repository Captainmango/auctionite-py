from django.urls import path
from . import views

urlpatterns = [
    path("items", views.CreateItemView.as_view(), name="items.create"),
]