from huey.contrib.djhuey import db_task
from django.conf import settings


@db_task()
def process_feature_request(feature_id: str):
    """
    Background task: generate embedding and extract AI fields for a FeatureRequest.
    Runs after submission so the user isn't blocked.
    """
    from .models import FeatureRequest
    from ai_services.embeddings import generate_embedding
    from ai_services.extraction import extract_fields

    try:
        feature = FeatureRequest.objects.get(id=feature_id)
    except FeatureRequest.DoesNotExist:
        return

    # Generate embedding
    try:
        text = f"{feature.title} {feature.description}"
        embedding = generate_embedding(text)
        feature.embedding = embedding
    except Exception:
        pass

    # Extract AI fields
    try:
        extracted = extract_fields(feature.title, feature.description, feature.segment)
        feature.category = extracted.get("category", "")
        feature.tags = extracted.get("tags", [])
        feature.sentiment = extracted.get("sentiment")
        feature.urgency = extracted.get("urgency")
    except Exception:
        pass

    feature.save(update_fields=["embedding", "category", "tags", "sentiment", "urgency", "updated_at"])
