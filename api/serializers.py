from rest_framework import serializers
from .models import ContentSection, ContactSubmission, LeaderboardEntry, GameItem


class ContentSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentSection
        fields = ["section_key", "data", "updated_at"]


class ContactSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = ["id", "submission_type", "form_data", "created_at"]
        read_only_fields = ["id", "created_at"]


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaderboardEntry
        fields = ["id", "name", "time", "created_at"]
        read_only_fields = ["id", "created_at"]


class GameItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameItem
        fields = ["id", "name", "recyclable", "created_at"]
        read_only_fields = ["id", "created_at"]
