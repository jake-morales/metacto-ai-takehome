import json
import numpy as np
from django.conf import settings
from django.utils import timezone
from .client import get_client
from .prompts import CLUSTER_LABEL_SYSTEM, CLUSTER_LABEL_USER


def run_clustering(run_id: str):
    """
    Fetches all FeatureRequests with embeddings, runs HDBSCAN clustering,
    creates Cluster + ClusterMembership records on the given ClusteringRun.
    Returns the ClusteringRun instance.
    """
    import hdbscan
    from features.models import FeatureRequest
    from clusters.models import ClusteringRun, Cluster, ClusterMembership

    run = ClusteringRun.objects.get(id=run_id)
    run.status = "running"
    run.save(update_fields=["status"])

    try:
        requests = list(
            FeatureRequest.objects.exclude(embedding=None).values(
                "id", "title", "description", "segment", "embedding"
            )
        )

        ids = [r["id"] for r in requests]
        embeddings = np.array([r["embedding"] for r in requests], dtype=np.float32)

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=max(3, len(requests) // 20),
            min_samples=2,
            metric="euclidean",
        )
        labels = clusterer.fit_predict(embeddings)
        probabilities = clusterer.probabilities_

        unique_labels = set(labels) - {-1}
        run.num_clusters = len(unique_labels)
        run.num_requests_processed = len(requests)

        # Group requests by cluster
        cluster_groups: dict[int, list] = {lbl: [] for lbl in unique_labels}
        for idx, lbl in enumerate(labels):
            if lbl != -1:
                cluster_groups[lbl].append((idx, probabilities[idx]))

        for lbl, members in cluster_groups.items():
            # Compute centroid
            member_indices = [m[0] for m in members]
            cluster_embeddings = embeddings[member_indices]
            centroid = cluster_embeddings.mean(axis=0)

            # Sample up to 10 representative requests for labeling
            sample_indices = sorted(members, key=lambda x: -x[1])[:10]
            sample_requests = [requests[m[0]] for m in sample_indices]
            samples_text = "\n".join(
                f"- [{r['segment']}] {r['title']}: {r['description'][:200]}"
                for r in sample_requests
            )

            label_data = _generate_cluster_label(len(members), samples_text)

            cluster = Cluster.objects.create(
                run=run,
                label=label_data.get("label", f"Cluster {lbl}"),
                summary=label_data.get("summary", ""),
                theme=label_data.get("theme", ""),
                request_count=len(members),
            )

            # Compute sentiment and vote stats
            fr_ids = [ids[m[0]] for m in members]
            from features.models import FeatureRequest as FR
            agg = FR.objects.filter(id__in=fr_ids).values_list("sentiment")
            sentiments = [s[0] for s in agg if s[0] is not None]
            if sentiments:
                cluster.avg_sentiment = sum(sentiments) / len(sentiments)
                cluster.save()

            memberships = []
            for idx, prob in members:
                dist = float(np.linalg.norm(embeddings[idx] - centroid))
                memberships.append(
                    ClusterMembership(
                        cluster=cluster,
                        request_id=ids[idx],
                        similarity_score=prob,
                    )
                )
            ClusterMembership.objects.bulk_create(memberships, ignore_conflicts=True)

        run.status = "completed"
        run.completed_at = timezone.now()
        run.save()

    except Exception as e:
        run.status = "failed"
        run.completed_at = timezone.now()
        run.save()
        raise

    return run


def _generate_cluster_label(count: int, samples_text: str) -> dict:
    client = get_client()
    try:
        response = client.chat.completions.create(
            model=settings.EXTRACTION_MODEL,
            messages=[
                {"role": "system", "content": CLUSTER_LABEL_SYSTEM},
                {"role": "user", "content": CLUSTER_LABEL_USER.format(count=count, samples=samples_text)},
            ],
            response_format={"type": "json_object"},
            max_tokens=150,
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"label": "Unnamed Cluster", "summary": "", "theme": ""}
