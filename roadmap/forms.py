from django import forms
from .models import RoadmapItem


class RoadmapItemForm(forms.ModelForm):
    class Meta:
        model = RoadmapItem
        fields = ["title", "description", "status", "target_date", "order"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500",
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "rows": 3,
            }),
            "status": forms.Select(attrs={
                "class": "w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500",
            }),
            "target_date": forms.DateInput(attrs={
                "type": "date",
                "class": "w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500",
            }),
            "order": forms.NumberInput(attrs={
                "class": "w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500",
            }),
        }
