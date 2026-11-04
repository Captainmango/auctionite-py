from django.urls import path

from . import views

urlpatterns = [
    path("auth/register", views.RegisterView.as_view(), name="users.register"),
    path("auth/login", views.LoginView.as_view(), name="users.login"),
    path("auth/me", views.MeDetailsView.as_view(), name="users.details"),
]
