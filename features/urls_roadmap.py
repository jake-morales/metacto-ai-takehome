from django.urls import path
from . import views_roadmap

urlpatterns = [
    path("", views_roadmap.customer_roadmap, name="customer_roadmap"),
    path("vote/<uuid:pk>/", views_roadmap.vote, name="vote"),
    path("unvote/<uuid:pk>/", views_roadmap.unvote, name="unvote"),
]
