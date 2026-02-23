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

from apps.accounts.permissions import IsAdmin
from apps.metrics.models import MetricEvent
from apps.metrics.schemas import (
    event_summary_schema,
    health_diagnostic_schema,
    health_schema,
)
from apps.metrics.serializers import EventSummarySerializer


@health_schema
@method_decorator(never_cache, name="dispatch")
class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        data = {
            "type": "health",
            "id": "api",
            "attributes": {
                "status": "ok",
                "version": getattr(settings, "API_VERSION", "unknown"),
            },
        }

        return Response(data)


@health_diagnostic_schema
@method_decorator(never_cache, name="dispatch")
class HealthDiagnosticView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        start = time.monotonic()
        try:
            with connections["default"].cursor():
                db = "ok"
        except OperationalError:
            db = "unavailable"

        return Response(
            {
                "type": "health",
                "id": "api",
                "attributes": {
                    "status": "ok",
                    "database": db,
                    "db_latency_ms": int((time.monotonic() - start) * 1000),
                },
            }
        )


@event_summary_schema
@method_decorator(never_cache, name="dispatch")
class EventSummaryView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timezone.timedelta(days=7)
        qs = MetricEvent.objects.values("event_type").annotate(
            total=Count("id"),
            last_7_days=Count("id", filter=Q(created_at__gte=week_start)),
            today=Count("id", filter=Q(created_at__gte=today_start)),
        )
        serializer = EventSummarySerializer(qs, many=True)
        return Response(serializer.data)
