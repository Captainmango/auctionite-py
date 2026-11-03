from typing import Any

from django.db.utils import IntegrityError
from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serialisers import RegisterRequestSerialiser, LoginRequestSerialiser


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterRequestSerialiser
    permission_classes = [permissions.AllowAny]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            return super().create(request, args, kwargs)
        except IntegrityError as e:
            return Response({"error": "Username taken"}, status=status.HTTP_409_CONFLICT)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request):
        serialiser = LoginRequestSerialiser(data=request.data, context={"request": request})
        serialiser.is_valid(raise_exception=True)
        user = serialiser.validated_data.get("user")
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": str(token)}, status=status.HTTP_200_OK)