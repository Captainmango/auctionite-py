from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.serialisers import RegisterRequestSerialiser, LoginRequestSerialiser


class AccountsController:
    def __init__(
            self,
            register_serialiser = None,
            login_serialiser = None,
    ):
        self._register_serialiser = register_serialiser or RegisterRequestSerialiser
        self._login_serialiser = login_serialiser or LoginRequestSerialiser

    def register_user(self, request: Request) -> Response:
        serialiser = self._register_serialiser(data=request.data)
        serialiser.is_valid(raise_exception=True)
        try:
            serialiser.save()
        except IntegrityError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(serialiser.data, status=status.HTTP_201_CREATED)

    def login_user(self, request: Request) -> Response:
        serialiser = self._login_serialiser(data=request.data, context={"request": request})
        serialiser.is_valid(raise_exception=True)
        user = serialiser.validated_data.get("user")
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": str(token)}, status=status.HTTP_200_OK)
