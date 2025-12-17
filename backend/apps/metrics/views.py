from django.conf import settings
from django.db import connections
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


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

        try:
            connections["default"].cursor()
            data["attributes"]["database"] = "ok"
        except Exception:
            data["database"] = "unavailable"

        return Response(data)
