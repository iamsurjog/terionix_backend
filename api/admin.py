from django.contrib import admin

from .models import ContentSection, ContactSubmission, GameItem, LeaderboardEntry, Tender


@admin.register(ContentSection)
class ContentSectionAdmin(admin.ModelAdmin):
    list_display = ["section_key", "updated_at"]
    search_fields = ["section_key"]
    readonly_fields = ["updated_at"]


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ["submission_type", "created_at"]
    list_filter = ["submission_type"]
    readonly_fields = ["submission_type", "form_data", "created_at"]


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ["name", "time", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name"]


@admin.register(GameItem)
class GameItemAdmin(admin.ModelAdmin):
    list_display = ["name", "recyclable"]
    list_filter = ["recyclable"]
    search_fields = ["name"]


@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = ["title", "serial_no", "organization_chain", "published_date", "created_at"]
    search_fields = ["title", "organization_chain"]
