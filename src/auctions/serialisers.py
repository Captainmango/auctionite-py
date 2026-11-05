from rest_framework import serializers

from auctions.models import Listing, ListingSchedule, ListingStateTransition
from items.serialisers import ItemSerialiser


class CreateListingRequest(serializers.Serializer):
    item_id = serializers.BigIntegerField(required=True)
    starting_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)


class ListingScheduleSerialiser(serializers.ModelSerializer):
    class Meta:
        model = ListingSchedule
        fields = "__all__"


class ListingStatusSerialiser(serializers.ModelSerializer):
    class Meta:
        model = ListingStateTransition
        fields = ["status", "created_at"]


class ListingSerialiser(serializers.ModelSerializer):
    item = ItemSerialiser()

    class Meta:
        model = Listing
        fields = ["id", "starting_price", "item"]


class ListingDetailsSerialiser(serializers.ModelSerializer):
    item = ItemSerialiser()
    scheduled_times = ListingScheduleSerialiser(many=True)
    current_status = serializers.SerializerMethodField()

    def get_current_status(self, obj):
        statuses = obj.status_changes
        return ListingStatusSerialiser(statuses[0]).data if statuses else None

    class Meta:
        model = Listing
        fields = ["id", "starting_price", "current_status", "scheduled_times", "item"]


class BidAmountSerialiser(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=True)