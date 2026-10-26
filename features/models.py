import uuid
from django.db import models
from pgvector.django import VectorField, HnswIndex


class FeatureRequest(models.Model):
    class Segment(models.TextChoices):
        USER = "user", "User"
        DRIVER = "driver", "Driver"
        MERCHANT = "merchant", "Merchant"

    class Status(models.TextChoices):
        NEW = "new", "New"
        UNDER_REVIEW = "under_review", "Under Review"
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In Progress"
        SHIPPED = "shipped", "Shipped"
        DECLINED = "declined", "Declined"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    description = models.TextField()
    submitter_name = models.CharField(max_length=200, blank=True)
    segment = models.CharField(max_length=20, choices=Segment.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    sentiment = models.FloatField(null=True, blank=True)
    urgency = models.FloatField(null=True, blank=True)
    embedding = VectorField(dimensions=3072, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            HnswIndex(
                name="feat_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]

    def __str__(self):
        return f"[{self.segment}] {self.title}"


class Vote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    roadmap_item = models.ForeignKey(
        "roadmap.RoadmapItem", on_delete=models.CASCADE, related_name="votes"
    )
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("roadmap_item", "session_key")]
