from django.shortcuts import render, redirect
from django.contrib import messages
from .models import FeatureRequest
from .forms import FeatureRequestForm


def submit_request(request):
    if request.method == "POST":
        form = FeatureRequestForm(request.POST)
        if form.is_valid():
            feature = form.save()
            # Kick off background tasks for embedding + extraction
            try:
                from .tasks import process_feature_request
                process_feature_request(str(feature.id))
            except Exception:
                pass  # Tasks are best-effort; don't block the user
            messages.success(
                request,
                f"Thanks! Your request '{feature.title}' has been submitted. "
                "Our team will review it soon."
            )
            return redirect("submit_request")
    else:
        form = FeatureRequestForm()

    return render(request, "features/submit.html", {"form": form})
