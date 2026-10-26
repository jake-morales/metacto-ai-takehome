import json
from django.conf import settings
from .client import get_client
from .prompts import EXTRACTION_SYSTEM, EXTRACTION_USER


def extract_fields(title: str, description: str, segment: str) -> dict:
    """
    Calls gpt-4o-mini to extract category, tags, sentiment, urgency from a feature request.
    Returns a dict with those keys (or safe defaults on failure).
    """
    client = get_client()
    user_msg = EXTRACTION_USER.format(
        title=title, description=description, segment=segment
    )
    try:
        response = client.chat.completions.create(
            model=settings.EXTRACTION_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=200,
            temperature=0.1,
        )
        data = json.loads(response.choices[0].message.content)
        return {
            "category": str(data.get("category", ""))[:100],
            "tags": data.get("tags", []) if isinstance(data.get("tags"), list) else [],
            "sentiment": float(data.get("sentiment", 0.0)),
            "urgency": float(data.get("urgency", 0.5)),
        }
    except Exception:
        return {"category": "", "tags": [], "sentiment": 0.0, "urgency": 0.5}
