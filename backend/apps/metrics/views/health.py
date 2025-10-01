from django.db import connections
from django.db.utils import OperationalError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class BaseHealthCheckView(APIView):
    def check_database(self):
        try:
            connections["default"].cursor()
            return "ok"
        except OperationalError:
            return "unavailable"

    def get_health_status(self):
        db_status = self.check_database()
        overall_status = "ok" if db_status == "ok" else "error"
        return {"status": overall_status, "database": db_status}

    def get(self, requests, format=None):
        data = self.get_health_status()
        http_status = (
            status.HTTP_200_OK
            if data["status"] == "ok"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(data, status=http_status)


class HealthCheckView(BaseHealthCheckView):
    pass


class FullHealthCheckView(BaseHealthCheckView):
    def get_health_status(self):
        data = super().get_health_status()
        data["placeholder_field"] = "ok"
        return data
