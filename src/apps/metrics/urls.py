from django.urls import path

from apps.metrics.views import (
    APIHealthView,
    DatabaseHealthView,
    MetricRecordView,
    StorageHealthView,
)

urlpatterns = [
    path("health/", APIHealthView.as_view(), name="health"),
    path("health/database/", DatabaseHealthView.as_view(), name="health_database"),
    path("metrics/", MetricRecordView.as_view(), name="metric_records"),
    path("health/storage/", StorageHealthView.as_view(), name="health_storage"),
]
