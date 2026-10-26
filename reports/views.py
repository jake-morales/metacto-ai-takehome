import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import ChatSession, ChatMessage
from ai_services.prompts import REPORT_INITIAL_PROMPT
from ai_services.reports import build_system_prompt, stream_chat_response


def session_list(request):
    sessions = ChatSession.objects.all()
    return render(request, "reports/session_list.html", {"sessions": sessions})


@require_POST
def create_session(request):
    system_prompt = build_system_prompt()
    now = timezone.now()
    title = now.strftime("%b %d, %Y %I:%M %p")
    session = ChatSession.objects.create(system_prompt=system_prompt, title=title)
    return redirect("report_chat", pk=session.pk)


def report_chat(request, pk):
    session = get_object_or_404(ChatSession, pk=pk)
    sessions = ChatSession.objects.all()
    messages = session.messages.all()
    # Pre-fill the prompt in the input for fresh sessions (no messages yet)
    is_fresh = messages.count() == 0
    # Still need to detect "sent first message, waiting for response"
    needs_initial_response = (
        messages.count() == 1 and messages.first().role == ChatMessage.Role.USER
    )
    return render(request, "reports/chat.html", {
        "session": session,
        "sessions": sessions,
        "messages": messages,
        "needs_initial_response": needs_initial_response,
        "initial_prompt": REPORT_INITIAL_PROMPT if is_fresh else "",
    })


ALLOWED_MODELS = {"gpt-6-sol"}

@require_POST
def send_message(request, pk):
    session = get_object_or_404(ChatSession, pk=pk)
    content = request.POST.get("content", "").strip()
    if not content:
        return redirect("report_chat", pk=pk)

    model = request.POST.get("model", "gpt-6-sol")
    if model in ALLOWED_MODELS and session.model != model:
        session.model = model
        session.save(update_fields=["model"])

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content=content,
    )
    return redirect("report_chat", pk=pk)


def stream_response(request, pk):
    """
    SSE endpoint. Streams the AI response for the latest user message.
    """
    session = get_object_or_404(ChatSession, pk=pk)

    response = StreamingHttpResponse(
        stream_chat_response(str(session.pk), model=session.model),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@require_POST
def delete_session(request, pk):
    session = get_object_or_404(ChatSession, pk=pk)
    session.delete()
    return redirect("report_session_list")


@require_POST
def rename_session(request, pk):
    session = get_object_or_404(ChatSession, pk=pk)
    title = request.POST.get("title", "").strip()
    if title:
        session.title = title[:300]
        session.save(update_fields=["title"])
    return redirect("report_chat", pk=pk)
