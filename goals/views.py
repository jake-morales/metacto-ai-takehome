from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CompanyGoals
from .forms import CompanyGoalsForm


def edit_goals(request):
    goals = CompanyGoals.get_or_create_singleton()
    if request.method == "POST":
        form = CompanyGoalsForm(request.POST, instance=goals)
        if form.is_valid():
            form.save()
            messages.success(request, "Goals saved successfully.")
            return redirect("edit_goals")
    else:
        form = CompanyGoalsForm(instance=goals)
    return render(request, "goals/edit.html", {"form": form, "goals": goals})
