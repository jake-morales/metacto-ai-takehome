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

    top_voted = RoadmapItem.objects.order_by("-vote_count")[:5]
    top_voted_text = "\n".join(
        f"- {item.title} ({item.vote_count} votes, status: {item.status})"
        for item in top_voted
    ) or "No roadmap items yet."

    latest_run = ClusteringRun.objects.filter(status="completed").order_by("-started_at").first()
    if latest_run:
        clusters = latest_run.clusters.order_by("-request_count")[:15]
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
        top_voted=top_voted_text,
        cluster_summaries=cluster_summaries,
    )


def stream_chat_response(session_id):
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

    # For follow-up questions (more than the initial), inject RAG context
    user_messages = [m for m in messages if m.role == "user"]
    if len(user_messages) > 1:
        latest_user_msg = user_messages[-1].content
        rag_context = _build_rag_context(latest_user_msg)
        # Insert RAG context as a system message just before the last user message
        for msg in messages[:-1]:
            openai_messages.append({"role": msg.role, "content": msg.content})
        openai_messages.append({"role": "system", "content": rag_context})
        openai_messages.append({"role": "user", "content": latest_user_msg})
    else:
        for msg in messages:
            openai_messages.append({"role": msg.role, "content": msg.content})

    client = get_client()
    full_response = []

    try:
        stream = client.chat.completions.create(
            model=settings.REPORT_MODEL,
            messages=openai_messages,
            stream=True,
            max_tokens=2000,
            temperature=0.4,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                token = delta.content
                full_response.append(token)
                # SSE format: "data: <token>\n\n"
                yield f"data: {token}\n\n"

        # Save complete assistant message
        complete_text = "".join(full_response)
        ChatMessage.objects.create(
            session=session,
            role="assistant",
            content=complete_text,
        )
        yield "data: [DONE]\n\n"

    except Exception as e:
        yield f"data: [ERROR] {str(e)}\n\n"


def _build_rag_context(question: str) -> str:
    try:
        embedding = generate_embedding(question)
        similar = search_similar_requests(embedding, top_k=20)
        if not similar:
            return ""
        requests_text = "\n".join(
            f"- [{r.segment}] {r.title}: {r.description[:300]}"
            for r in similar
        )
        return RAG_CONTEXT_INJECTION.format(count=len(similar), requests=requests_text)
    except Exception:
        return ""
