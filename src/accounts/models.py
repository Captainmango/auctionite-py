from __future__ import annotations

from typing import Any, Optional, TypeVar

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db.utils import IntegrityError

_T = TypeVar("_T", bound=AbstractUser)


class UserManager(DjangoUserManager[_T]):
    use_in_migrations = False

    def create_user(
        self,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **extra_fields: Any,
    ) -> _T:
        if not email:
            raise ValueError("Email required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        try:
            user.save(using=self._db)
        except IntegrityError as e:
            raise e
        return user

    def create_superuser(
        self,
        username: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **extra_fields: Any,
    ) -> _T:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    objects = UserManager()

    class Meta:
        db_table = "users"
