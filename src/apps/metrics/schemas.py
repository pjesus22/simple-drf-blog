from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    PolymorphicProxySerializer,
    extend_schema,
)

from apps.metrics.serializers import (
    DiagnosticHealthSerializer,
    HealthSerializer,
    MetricEventSerializer,
    MetricEventSummarySerializer,
    StorageHealthSerializer,
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

metric_event_schema = extend_schema(
    summary="metric_event",
    description=("List all metric events (requires admin role). "),
    parameters=[
        OpenApiParameter(
            name="summary",
            type=str,
            description="Pass 'true' to get event counts grouped by event type.",
            required=False,
            enum=["true", "false"],
        )
    ],
    responses={
        200: PolymorphicProxySerializer(
            component_name="MetricEventResponse",
            serializers=[
                MetricEventSerializer,
                MetricEventSummarySerializer,
            ],
            resource_type_field_name=None,
        )
    },
)


storage_health_schema = extend_schema(
    summary="health_storage",
    description=(
        "Checks whether the active media storage backend (local, S3, or GCS) "
        "is reachable and writable. Requires admin role."
    ),
    responses={
        200: StorageHealthSerializer,
        503: OpenApiResponse(description="Storage backend unreachable"),
    },
)
