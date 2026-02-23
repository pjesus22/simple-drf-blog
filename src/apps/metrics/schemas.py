from drf_spectacular.utils import extend_schema

from apps.metrics.serializers import (
    DiagnosticHealthSerializer,
    EventSummarySerializer,
    HealthSerializer,
)

health_schema = extend_schema(
    summary="health",
    description="Health check endpoint.",
    responses={200: HealthSerializer},
)

health_diagnostic_schema = extend_schema(
    summary="health_diagnostic",
    description=(
        "Health check endpoint with database diagnostics (requires admin role)."
    ),
    responses={200: DiagnosticHealthSerializer},
)

event_summary_schema = extend_schema(
    summary="metrics_summary",
    description=(
        "Event counts grouped by type: total, last 7 days, and today."
        "Requires admin (requires Admin role)."
    ),
    responses={200: EventSummarySerializer},
)
