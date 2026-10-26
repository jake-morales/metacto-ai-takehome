from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.db import transaction
from roadmap.models import RoadmapItem
from .models import Vote


def customer_roadmap(request):
    # Ensure the user has a session key
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    items = RoadmapItem.objects.all()
    voted_ids = set(
        Vote.objects.filter(session_key=session_key)
        .values_list("roadmap_item_id", flat=True)
    )

    def with_vote(item):
        return {"item": item, "voted": item.pk in voted_ids}

    planned = [with_vote(i) for i in items if i.status == RoadmapItem.Status.PLANNED]
    in_progress = [with_vote(i) for i in items if i.status == RoadmapItem.Status.IN_PROGRESS]
    shipped = [with_vote(i) for i in items if i.status == RoadmapItem.Status.SHIPPED]

    context = {
        "planned": planned,
        "in_progress": in_progress,
        "shipped": shipped,
    }
    return render(request, "features/roadmap.html", context)


@require_POST
def vote(request, pk):
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    item = get_object_or_404(RoadmapItem, pk=pk)

    with transaction.atomic():
        _, created = Vote.objects.get_or_create(
            roadmap_item=item, session_key=session_key
        )
        if created:
            RoadmapItem.objects.filter(pk=pk).update(vote_count=item.vote_count + 1)
            item.refresh_from_db()

    return render(
        request,
        "features/partials/vote_button.html",
        {"item": item, "voted": True},
    )


@require_POST
def unvote(request, pk):
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    item = get_object_or_404(RoadmapItem, pk=pk)

    with transaction.atomic():
        deleted, _ = Vote.objects.filter(
            roadmap_item=item, session_key=session_key
        ).delete()
        if deleted:
            new_count = max(0, item.vote_count - 1)
            RoadmapItem.objects.filter(pk=pk).update(vote_count=new_count)
            item.refresh_from_db()

    return render(
        request,
        "features/partials/vote_button.html",
        {"item": item, "voted": False},
    )
