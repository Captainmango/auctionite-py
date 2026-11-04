from typing import Any

from django.db.utils import IntegrityError
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .controllers import AccountsController
from .serialisers import RegisterRequestSerialiser, LoginRequestSerialiser


_auth_controller = AccountsController()

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        return _auth_controller.register_user(request)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        return _auth_controller.login_user(request)