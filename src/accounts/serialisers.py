from typing import Any

from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User
from src.common.errors import ValidationErr


class RegisterSerialiser(serializers.ModelSerializer):
    password = serializers.CharField(required=True, write_only=True, min_length=6)
    username = serializers.CharField(required=True, write_only=True)
    email = serializers.EmailField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "password", "username"]

    def create(self, validated_data: Any) -> User:
        return User.objects.create_user(**validated_data)


class LoginSerialiser(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> Any:
        user = authenticate(
            request=self.context.get("request"),
            username=attrs.get("username"),
            password=attrs.get("password"),
        )
        if not user:
            raise ValidationErr("Invalid credentials")
        attrs["user"] = user
        return attrs