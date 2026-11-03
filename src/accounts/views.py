from rest_framework import generics, permissions
from .serialisers import RegisterSerialiser


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerialiser
    permission_classes = [permissions.AllowAny]
