from rest_framework import status
from rest_framework.exceptions import ValidationError


class ValidationErr(ValidationError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY