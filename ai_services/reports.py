from django.conf import settings
from .client import get_client
from .prompts import REPORT_SYSTEM, REPORT_INITIAL_PROMPT, RAG_CONTEXT_INJECTION
from .embeddings import generate_embedding, search_similar_requests


def build_system_prompt() -> str:
    """
    Assembles the system prompt from company goals, cluster summaries, and aggregate stats.
    Called when creating a new ChatSession.
    """
    from goals.models import CompanyGoals
    from features.models import FeatureRequest
    from clusters.models import ClusteringRun
    from roadmap.models import RoadmapItem

    goals_obj = CompanyGoals.get_or_create_singleton()
    mission_and_goals = f"Mission: {goals_obj.mission}\n\nGoals:\n{goals_obj.goals}" if (goals_obj.mission or goals_obj.goals) else "Not yet defined."

    segment_counts = {
        "user": FeatureRequest.objects.filter(segment="user").count(),
        "driver": FeatureRequest.objects.filter(segment="driver").count(),
        "merchant": FeatureRequest.objects.filter(segment="merchant").count(),
    }
    total = sum(segment_counts.values())

    roadmap_items = RoadmapItem.objects.order_by("-vote_count")
    if roadmap_items.exists():
        roadmap_text = "\n".join(
            f"- [{item.status}] {item.title} — {item.vote_count} votes"
            + (f"\n  {item.description}" if item.description else "")
            for item in roadmap_items
        )
    else:
        roadmap_text = "No roadmap items yet."

    latest_run = ClusteringRun.objects.filter(status="completed").order_by("-started_at").first()
    if latest_run:
        clusters = latest_run.clusters.order_by("-request_count")
        cluster_summaries = "\n\n".join(
            f"**{c.label}** ({c.request_count} requests, theme: {c.theme})\n{c.summary}"
            for c in clusters
        )
    else:
        cluster_summaries = "Clustering has not been run yet."

    return REPORT_SYSTEM.format(
        mission_and_goals=mission_and_goals,
        total_requests=total,
        user_count=segment_counts["user"],
        driver_count=segment_counts["driver"],
        merchant_count=segment_counts["merchant"],
        roadmap_items=roadmap_text,
        cluster_summaries=cluster_summaries,
    )


def stream_chat_response(session_id, model=None):
    """
    Generator that yields SSE-formatted strings.
    Fetches the session's message history, optionally injects RAG context,
    calls gpt-6-sol with stream=True, and yields chunks.
    Also saves the complete assistant message to the DB after streaming.
    """
    from reports.models import ChatSession, ChatMessage

    session = ChatSession.objects.get(id=session_id)
    messages = list(session.messages.order_by("created_at"))

    openai_messages = [{"role": "system", "content": session.system_prompt}]

    client = get_client()
    full_response = []
    input_tokens = None
    output_tokens = None
    rag_used = False
    rag_result_count = None

    # For follow-up questions (more than the initial), inject RAG context
    user_messages = [m for m in messages if m.role == "user"]
    if len(user_messages) > 1:
        latest_user_msg = user_messages[-1].content
        rag_context, rag_count = _build_rag_context(latest_user_msg)
        if rag_context:
            rag_used = True
            rag_result_count = rag_count
        for msg in messages[:-1]:
            openai_messages.append({"role": msg.role, "content": msg.content})
        if rag_context:
            openai_messages.append({"role": "system", "content": rag_context})
        openai_messages.append({"role": "user", "content": latest_user_msg})
    else:
        for msg in messages:
            openai_messages.append({"role": msg.role, "content": msg.content})

    try:
        stream = client.chat.completions.create(
            model=model or settings.REPORT_MODEL,
            messages=openai_messages,
            stream=True,
            max_completion_tokens=2000,
            stream_options={"include_usage": True},
        )

        for chunk in stream:
            if chunk.usage:
                input_tokens = chunk.usage.prompt_tokens
                output_tokens = chunk.usage.completion_tokens
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                token = delta.content
                full_response.append(token)
                yield f"data: {token}\n\n"

        # Save complete assistant message with token counts
        complete_text = "".join(full_response)
        ChatMessage.objects.create(
            session=session,
            role="assistant",
            content=complete_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            rag_used=rag_used,
            rag_result_count=rag_result_count,
        )
        yield "data: [DONE]\n\n"

    except Exception as e:
        yield f"data: [ERROR] {str(e)}\n\n"


def _build_rag_context(question: str) -> tuple[str, int]:
    try:
        embedding = generate_embedding(question)
        similar = search_similar_requests(embedding, top_k=20)
        if not similar:
            return "", 0
        requests_text = "\n".join(
            f"- [{r.segment}] {r.title}: {r.description[:300]}"
            for r in similar
        )
        return RAG_CONTEXT_INJECTION.format(count=len(similar), requests=requests_text), len(similar)
    except Exception:
        return "", 0
