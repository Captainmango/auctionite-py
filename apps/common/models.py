from django.db import models


class BaseModel(models.Model):
    id = models.BigAutoField()
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=True)