from __future__ import annotations

from typing import Optional

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.utils import IntegrityError


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: Optional[str] = None, **kwargs) -> "User":
        if not email:
            raise ValueError("Email required")
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        try:
            user.save(using=self._db)
        except IntegrityError as e:
            raise e
        return user

    def create_superuser(self, email, password=None, **kwargs):
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        return self.create_user(email, password, **kwargs)


class User(AbstractUser):
    objects = UserManager()

