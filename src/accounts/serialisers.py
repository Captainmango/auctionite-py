from typing import Any

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from config import settings
from .models import User


class RegisterRequestSerialiser(serializers.ModelSerializer):
    password = serializers.CharField(required=True, write_only=True, min_length=6)
    username = serializers.CharField(required=True, write_only=True)
    email = serializers.EmailField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "password", "username"]

    def create(self, validated_data: Any) -> User:
        return User.objects.create_user(**validated_data)


class LoginRequestSerialiser(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> Any:
        user = authenticate(
            request=self.context.get("request"),
            username=attrs.get("username"),
            password=attrs.get("password"),
        )
        if not user:
            raise ValidationError("Invalid credentials")
        attrs["user"] = user
        return attrs


class UserSerialiser(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "first_name", "last_name", "email"]