from rest_framework import serializers
from .models import ContentSection, ContactSubmission, EmailConfig, LeaderboardEntry, GameItem


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


class EmailConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailConfig
        fields = ["id", "to_email", "smtp_host", "smtp_port", "smtp_user", "smtp_password", "use_tls", "updated_at"]
        read_only_fields = ["id", "updated_at"]
        extra_kwargs = {
            "smtp_password": {"write_only": True},
        }
