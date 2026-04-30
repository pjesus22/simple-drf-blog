import time

from django.conf import settings
from django.db import connections
from django.db.models import Count, Q
from django.db.utils import OperationalError
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_json_api.renderers import JSONRenderer

from apps.accounts.permissions import IsAdmin
from apps.metrics.models import MetricEvent
from apps.metrics.schemas import (
    health_diagnostic_schema,
    health_schema,
    metric_event_schema,
    storage_health_schema,
)
from apps.metrics.serializers import (
    APIHealthSerializer,
    DatabaseHealthSerializer,
    MetricEventSerializer,
    MetricEventSummarySerializer,
    StorageHealthSerializer,
)
from apps.uploads.storage import get_media_storage


@health_schema
@method_decorator(never_cache, name="dispatch")
class APIHealthView(APIView):
    permission_classes = [AllowAny]
    resource_name = "health"
    renderer_classes = [JSONRenderer]

    def get(self, request, *args, **kwargs):
        data = {
            "status": "ok",
            "version": getattr(settings, "API_VERSION", "unknown"),
        }

        serializer = APIHealthSerializer(data)

        response_data = serializer.data
        response_data["id"] = "api"

        return Response(response_data)


@health_diagnostic_schema
@method_decorator(never_cache, name="dispatch")
class DatabaseHealthView(APIView):
    permission_classes = [IsAdmin]
    resource_name = "health"
    renderer_classes = [JSONRenderer]

    def get(self, request):
        start = time.monotonic()
        try:
            with connections["default"].cursor():
                db_status = "ok"
        except OperationalError:
            db_status = "unavailable"

        data = {
            "status": "ok",
            "version": getattr(settings, "API_VERSION", "unknown"),
            "db_status": db_status,
            "db_latency_ms": int((time.monotonic() - start) * 1000),
        }

        serializer = DatabaseHealthSerializer(data)
        response_data = serializer.data
        response_data["id"] = "database"

        return Response(response_data)


@metric_event_schema
class MetricEventView(APIView):
    permission_classes = [IsAdmin]
    resource_name = "metric-events"
    renderer_classes = [JSONRenderer]

    def get(self, request):
        summary = request.query_params.get("summary") == "true"
        if summary:
            self.resource_name = "metric-event-summaries"
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = now - timezone.timedelta(days=7)
            qs = MetricEvent.objects.values("event_type").annotate(
                total=Count("id"),
                last_7_days=Count("id", filter=Q(created_at__gte=week_start)),
                today=Count("id", filter=Q(created_at__gte=today_start)),
            )
            serializer = MetricEventSummarySerializer(qs, many=True)
            return Response(serializer.data)

        qs = MetricEvent.objects.all()
        serializer = MetricEventSerializer(qs, many=True)
        return Response(serializer.data)


@storage_health_schema
@method_decorator(never_cache, name="dispatch")
class StorageHealthView(APIView):
    permission_classes = [IsAdmin]
    resource_name = "health"
    renderer_classes = [JSONRenderer]

    def get(self, request):
        storage = get_media_storage()
        reachable = storage.health_check()

        data = {
            "status": "ok" if reachable else "unavailable",
            "backend": storage.get_backend_name(),
            "reachable": reachable,
        }

        serializer = StorageHealthSerializer(data)
        response_data = serializer.data
        response_data["id"] = "storage"

        return Response(response_data, status=200 if reachable else 503)
