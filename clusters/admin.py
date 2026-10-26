from django.contrib import admin
from .models import ClusteringRun, Cluster, ClusterMembership


@admin.register(ClusteringRun)
class ClusteringRunAdmin(admin.ModelAdmin):
    list_display = ["id", "status", "num_clusters", "num_requests_processed", "started_at"]


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ["label", "theme", "request_count", "avg_sentiment"]
    list_filter = ["run"]


@admin.register(ClusterMembership)
class ClusterMembershipAdmin(admin.ModelAdmin):
    list_display = ["cluster", "request", "similarity_score"]
