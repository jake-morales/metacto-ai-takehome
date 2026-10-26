from django.urls import path
from . import views

urlpatterns = [
    path("", views.submit_request, name="submit_request"),
]
