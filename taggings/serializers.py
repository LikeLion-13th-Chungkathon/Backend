from rest_framework import serializers
from .models import Tagging

class TaggingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tagging
        fields = "__all__"
        read_only_fields = ["id", "user", "memo"]

        