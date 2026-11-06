from rest_framework import serializers

from accounts.serialisers import UserSerialiser
from items.models import Item, ItemPictures


class UpsertItemRequest(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=200)
    description = serializers.CharField(max_length=255)
    pictures = serializers.ListField(
        required=False,
        child=serializers.ImageField(),
        allow_empty=True,
        max_length=5,
    )


class ItemPicturesSerialiser(serializers.ModelSerializer):
    class Meta:
        model = ItemPictures
        fields = ["blob", "sort_order"]


class ItemSerialiser(serializers.Serializer):
    item_pictures = ItemPicturesSerialiser(many=True)
    owner = UserSerialiser()

    class Meta:
        model = Item
        fields = ["owner", "item_pictures", "name", "description"]
