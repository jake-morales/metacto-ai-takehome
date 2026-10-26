import uuid
from django.db import models


class ClusteringRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    num_clusters = models.PositiveIntegerField(null=True, blank=True)
    num_requests_processed = models.PositiveIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Clustering Run {self.started_at:%Y-%m-%d %H:%M} — {self.status}"


class Cluster(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(ClusteringRun, on_delete=models.CASCADE, related_name="clusters")
    label = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    theme = models.CharField(max_length=100, blank=True)
    requests = models.ManyToManyField(
        "features.FeatureRequest", through="ClusterMembership", related_name="clusters"
    )
    request_count = models.PositiveIntegerField(default=0)
    avg_sentiment = models.FloatField(null=True, blank=True)
    total_votes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-request_count"]

    def __str__(self):
        return self.label


class ClusterMembership(models.Model):
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    request = models.ForeignKey("features.FeatureRequest", on_delete=models.CASCADE)
    similarity_score = models.FloatField(default=0.0)

    class Meta:
        unique_together = [("cluster", "request")]
