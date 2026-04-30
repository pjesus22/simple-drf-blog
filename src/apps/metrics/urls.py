from django.urls import path

from apps.metrics.views import (
    APIHealthView,
    DatabaseHealthView,
    MetricEventView,
    StorageHealthView,
)

urlpatterns = [
    path("health/", APIHealthView.as_view(), name="health"),
    path("health/database/", DatabaseHealthView.as_view(), name="health_database"),
    path("metrics/", MetricEventView.as_view(), name="metrics"),
    path("health/storage/", StorageHealthView.as_view(), name="health_storage"),
]
