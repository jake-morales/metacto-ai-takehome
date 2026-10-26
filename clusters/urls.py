from django.urls import path
from . import views

urlpatterns = [
    path("", views.cluster_list, name="cluster_list"),
    path("trigger/", views.trigger_clustering, name="trigger_clustering"),
    path("<uuid:pk>/", views.cluster_detail, name="cluster_detail"),
]
