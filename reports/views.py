import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ChatSession, ChatMessage
from ai_services.prompts import REPORT_INITIAL_PROMPT
from ai_services.reports import build_system_prompt, stream_chat_response


def session_list(request):
    sessions = ChatSession.objects.all()
    return render(request, "reports/session_list.html", {"sessions": sessions})


@require_POST
def create_session(request):
    system_prompt = build_system_prompt()
    session = ChatSession.objects.create(system_prompt=system_prompt)
    # Save pre-loaded user prompt as first message
    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content=REPORT_INITIAL_PROMPT,
    )
    return redirect("report_chat", pk=session.pk)


def report_chat(request, pk):
    session = get_object_or_404(ChatSession, pk=pk)
    sessions = ChatSession.objects.all()
    messages = session.messages.all()
    # Check if first message has a response yet
    needs_initial_response = (
        messages.count() == 1 and messages.first().role == ChatMessage.Role.USER
    )
    return render(request, "reports/chat.html", {
        "session": session,
        "sessions": sessions,
        "messages": messages,
        "needs_initial_response": needs_initial_response,
        "initial_prompt": REPORT_INITIAL_PROMPT,
    })


@require_POST
def send_message(request, pk):
    session = get_object_or_404(ChatSession, pk=pk)
    content = request.POST.get("content", "").strip()
    if not content:
        return redirect("report_chat", pk=pk)

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
        stream_chat_response(str(session.pk)),
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
