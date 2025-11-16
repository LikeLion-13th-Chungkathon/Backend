from rest_framework import serializers
from .models import Tagging, TagStyle

class TaggingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tagging
        fields = "__all__"
        read_only_fields = ["id", "user", "memo"]

class TagStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagStyle
        fields = ["id", "tag_detail", "tag_color"]
        read_only_fields = ["id"]