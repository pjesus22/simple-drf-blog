from django.urls import path

from .views import HealthDiagnosticView, HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path(
        "health/diagnostic/", HealthDiagnosticView.as_view(), name="health_diagnostic"
    ),
]
