from django import forms
from .models import CompanyGoals


class CompanyGoalsForm(forms.ModelForm):
    class Meta:
        model = CompanyGoals
        fields = ["mission", "goals"]
        widgets = {
            "mission": forms.Textarea(attrs={
                "class": "w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "rows": 4,
                "placeholder": "e.g. To make food delivery fast, affordable, and delightful for everyone in the city.",
            }),
            "goals": forms.Textarea(attrs={
                "class": "w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "rows": 8,
                "placeholder": "List your product goals, one per line or as bullet points.\ne.g.\n- Grow merchant count by 30%\n- Reduce driver churn by 20%\n- Improve order accuracy to 99%",
            }),
        }
