from django.urls import path
from . import views

urlpatterns = [
    path("", views.edit_goals, name="edit_goals"),
]
