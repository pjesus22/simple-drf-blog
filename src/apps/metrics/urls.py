from django.urls import path

from apps.metrics.views import (
    EventSummaryView,
    HealthDiagnosticView,
    HealthView,
    StorageHealthView,
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path(
        "health/diagnostic/", HealthDiagnosticView.as_view(), name="health_diagnostic"
    ),
    path("metrics/summary/", EventSummaryView.as_view(), name="metrics_summary"),
    path("health/storage/", StorageHealthView.as_view(), name="health_storage"),
]
