import time

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin


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
