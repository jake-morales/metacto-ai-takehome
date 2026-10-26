from django.conf import settings
from .client import get_client


def generate_embedding(text: str) -> list[float]:
    client = get_client()
    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def search_similar_requests(query_embedding: list[float], top_k: int = 20, exclude_id=None):
    """
    Returns FeatureRequest queryset ordered by cosine similarity to query_embedding.
    Uses pgvector's <=> operator (cosine distance).
    """
    from pgvector.django import CosineDistance
    from features.models import FeatureRequest

    qs = FeatureRequest.objects.exclude(embedding=None)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)

    return (
        qs.annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:top_k]
    )
