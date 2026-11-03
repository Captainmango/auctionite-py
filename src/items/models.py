from django.db import models

from common.models import BaseModel
from config import settings


class Item(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, blank=False)
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=False)

    class Meta:
        indexes = [
            models.Index(fields=["owner_id"])
        ]


class ItemPictures(BaseModel):
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING)
    blob = models.BinaryField()
    sort_order = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["item_id", "sort_order"])
        ]