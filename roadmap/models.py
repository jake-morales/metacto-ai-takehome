import uuid
from django.db import models


class RoadmapItem(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In Progress"
        SHIPPED = "shipped", "Shipped"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    order = models.PositiveIntegerField(default=0)
    vote_count = models.PositiveIntegerField(default=0)
    linked_requests = models.ManyToManyField(
        "features.FeatureRequest", blank=True, related_name="roadmap_items"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title
