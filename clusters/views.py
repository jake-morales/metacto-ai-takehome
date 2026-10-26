from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import ClusteringRun, Cluster


def cluster_list(request):
    latest_run = ClusteringRun.objects.filter(status="completed").first()
    all_runs = ClusteringRun.objects.all()[:5]
    clusters = latest_run.clusters.order_by("-request_count") if latest_run else []

    context = {
        "latest_run": latest_run,
        "all_runs": all_runs,
        "clusters": clusters,
    }
    return render(request, "clusters/list.html", context)


def cluster_detail(request, pk):
    cluster = get_object_or_404(Cluster, pk=pk)
    # Get sample members ordered by similarity score (higher = more representative)
    memberships = cluster.clustermembership_set.select_related("request").order_by(
        "-similarity_score"
    )[:20]
    samples = [m.request for m in memberships]

    context = {"cluster": cluster, "samples": samples}
    return render(request, "clusters/detail.html", context)


@require_POST
def trigger_clustering(request):
    from clusters.tasks import run_clustering_task
    from .models import ClusteringRun

    run = ClusteringRun.objects.create(status="pending")
    run_clustering_task(str(run.id))
    return redirect("cluster_list")
