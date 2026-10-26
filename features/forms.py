from django import forms
from .models import FeatureRequest


class FeatureRequestForm(forms.ModelForm):
    class Meta:
        model = FeatureRequest
        fields = ["title", "segment", "description", "submitter_name"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400",
                "placeholder": "e.g. Add scheduled order delivery",
            }),
            "segment": forms.Select(attrs={
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400",
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400",
                "rows": 5,
                "placeholder": "Describe the feature you'd like to see and why it would help you...",
            }),
            "submitter_name": forms.TextInput(attrs={
                "class": "w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400",
                "placeholder": "Your name (optional)",
            }),
        }
        labels = {
            "segment": "I am a...",
            "submitter_name": "Your name (optional)",
        }
