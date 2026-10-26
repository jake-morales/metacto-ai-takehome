from django.contrib import admin
from .models import FeatureRequest, Vote


@admin.register(FeatureRequest)
class FeatureRequestAdmin(admin.ModelAdmin):
    list_display = ["title", "segment", "status", "category", "sentiment", "urgency", "created_at"]
    list_filter = ["segment", "status", "category"]
    search_fields = ["title", "description"]
    readonly_fields = ["embedding", "created_at", "updated_at"]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["roadmap_item", "session_key", "created_at"]
