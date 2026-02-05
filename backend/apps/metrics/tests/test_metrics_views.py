from apps.accounts.permissions import IsAdmin
from apps.metrics.views import HealthDiagnosticView, HealthView
from django.db.utils import OperationalError
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory, force_authenticate

factory = APIRequestFactory()


class TestHealthView:
    def test_health_view_gets_permissions(self):
        view = HealthView()
        permissions = view.get_permissions()

        assert len(permissions) == 1
        assert isinstance(permissions[0], AllowAny)

    def test_health_view_success(self, settings):
        request = factory.get("/health/")
        response = HealthView.as_view()(request)

        assert response.status_code == 200
        assert response.data["type"] == "health"
        assert response.data["id"] == "api"
        assert response.data["attributes"]["status"] == "ok"
        assert response.data["attributes"]["version"] == "1.0"


class TestHealthDiagnosticView:
    def test_health_view_gets_permissions(self):
        view = HealthDiagnosticView()
        permissions = view.get_permissions()

        print(permissions)

        assert len(permissions) == 1
        assert isinstance(permissions[0], IsAdmin)

    def test_health_diagnostic_view_success(self, db, mocker):
        user = mocker.Mock()
        user.is_authenticated = True
        user.role = "admin"

        request = factory.get("/health/diagnostic/")
        force_authenticate(request, user)

        response = HealthDiagnosticView.as_view()(request)

        assert response.status_code == 200
        assert response.data["attributes"]["status"] == "ok"
        assert "database" in response.data["attributes"]
        assert response.data["attributes"]["database"] == "ok"
        assert "db_latency_ms" in response.data["attributes"]

    def test_health_diagnostic_view_database_unavailable(self, db, mocker):
        user = mocker.Mock()
        user.is_authenticated = True
        user.role = "admin"

        cursor = mocker.MagicMock()
        cursor.__enter__.side_effect = OperationalError()

        mocker.patch("apps.metrics.views.connections")[
            "default"
        ].cursor.return_value = cursor

        request = factory.get("/health/diagnostic/")
        force_authenticate(request, user=user)

        response = HealthDiagnosticView.as_view()(request)

        assert response.status_code == 200
        assert response.data["attributes"]["database"] == "unavailable"
