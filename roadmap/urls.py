from django.urls import path
from . import views

urlpatterns = [
    path("", views.edit_roadmap, name="edit_roadmap"),
    path("create/", views.create_item, name="create_roadmap_item"),
    path("<uuid:pk>/edit/", views.edit_item, name="edit_roadmap_item"),
    path("<uuid:pk>/delete/", views.delete_item, name="delete_roadmap_item"),
    path("<uuid:pk>/link/", views.link_request, name="link_request_to_roadmap"),
]
