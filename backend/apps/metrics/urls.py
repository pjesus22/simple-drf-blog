from django.urls import path

from .views import FullHealthCheckView, HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="healthcheck"),
    path("health/full/", FullHealthCheckView.as_view(), name="full_healthcheck"),
]
