from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="/submit/", permanent=False)),
    path("submit/", include("features.urls")),
    path("roadmap/", include("features.urls_roadmap")),
    path("internal/roadmap/", include("roadmap.urls")),
    path("internal/goals/", include("goals.urls")),
    path("internal/reports/", include("reports.urls")),
    path("internal/clusters/", include("clusters.urls")),
]
