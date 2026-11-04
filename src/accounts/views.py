from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .controllers import AccountsController


_auth_controller = AccountsController()

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        return _auth_controller.register_user(request)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        return _auth_controller.login_user(request)


class MeDetailsView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        return _auth_controller.me_details(request)