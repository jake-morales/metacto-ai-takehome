from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods
from django.http import HttpResponse
from .models import RoadmapItem
from .forms import RoadmapItemForm
from features.models import FeatureRequest


def edit_roadmap(request):
    items = RoadmapItem.objects.prefetch_related("linked_requests").all()
    form = RoadmapItemForm()
    return render(request, "roadmap/edit.html", {"items": items, "form": form})


@require_POST
def create_item(request):
    form = RoadmapItemForm(request.POST)
    if form.is_valid():
        form.save()
    return redirect("edit_roadmap")


@require_http_methods(["GET", "POST"])
def edit_item(request, pk):
    item = get_object_or_404(RoadmapItem, pk=pk)
    if request.method == "POST":
        form = RoadmapItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                items = RoadmapItem.objects.all()
                return render(request, "roadmap/partials/items_list.html", {"items": items})
            return redirect("edit_roadmap")
    else:
        form = RoadmapItemForm(instance=item)
    return render(request, "roadmap/partials/edit_form.html", {"form": form, "item": item})


@require_POST
def delete_item(request, pk):
    item = get_object_or_404(RoadmapItem, pk=pk)
    item.delete()
    if request.headers.get("HX-Request"):
        items = RoadmapItem.objects.all()
        return render(request, "roadmap/partials/items_list.html", {"items": items})
    return redirect("edit_roadmap")


@require_POST
def link_request(request, pk):
    item = get_object_or_404(RoadmapItem, pk=pk)
    request_id = request.POST.get("request_id")
    if request_id:
        try:
            fr = FeatureRequest.objects.get(pk=request_id)
            item.linked_requests.add(fr)
        except FeatureRequest.DoesNotExist:
            pass
    return redirect("edit_roadmap")
