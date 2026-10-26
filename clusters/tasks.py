from huey.contrib.djhuey import db_task


@db_task()
def run_clustering_task(run_id: str):
    from ai_services.clustering import run_clustering
    from clusters.models import ClusteringRun

    try:
        run_clustering()
    except Exception as e:
        ClusteringRun.objects.filter(id=run_id).update(status="failed")
        raise
