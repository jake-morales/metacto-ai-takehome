from django.contrib import admin
from .models import RoadmapItem


@admin.register(RoadmapItem)
class RoadmapItemAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "order", "vote_count", "created_at"]
    list_filter = ["status"]
    search_fields = ["title", "description"]
