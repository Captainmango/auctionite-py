from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("register", views.RegisterView.as_view(), name="users.register"),
    path("login", views.LoginView.as_view(), name="users.login"),
]