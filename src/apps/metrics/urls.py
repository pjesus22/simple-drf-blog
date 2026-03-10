from django.urls import path

from apps.metrics.views import (
    HealthDiagnosticView,
    HealthView,
    MetricEventView,
    StorageHealthView,
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path(
        "health/diagnostic/", HealthDiagnosticView.as_view(), name="health_diagnostic"
    ),
    path("metrics/", MetricEventView.as_view(), name="metrics"),
    path("health/storage/", StorageHealthView.as_view(), name="health_storage"),
]
