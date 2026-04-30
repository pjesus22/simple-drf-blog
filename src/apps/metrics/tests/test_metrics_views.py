from django.db.utils import OperationalError
import pytest
from rest_framework.permissions import AllowAny
from rest_framework.test import APIClient

from apps.accounts.permissions import IsAdmin
from apps.metrics.views import (
    APIHealthView,
    DatabaseHealthView,
    MetricEventView,
    StorageHealthView,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(mocker):
    user = mocker.Mock()
    user.is_authenticated = True
    user.role = "admin"
    return user


class TestHealthView:
    def test_health_view_permissions(self):
        view = APIHealthView()
        permissions = view.get_permissions()

        assert len(permissions) == 1
        assert isinstance(permissions[0], AllowAny)

    def test_health_view_get_success(self, api_client):
        response = api_client.get("/health/")
        data = response.json().get("data")

        assert response.status_code == 200
        assert data["type"] == "health"
        assert data["id"] == "api"
        assert data["attributes"]["status"] == "ok"
        assert data["attributes"]["version"] == "1.0"


class TestDatabaseHealthView:
    def test_database_health_view_permissions(self):
        view = DatabaseHealthView()
        permissions = view.get_permissions()

        assert len(permissions) == 1
        assert isinstance(permissions[0], IsAdmin)

    def test_database_health_view_get_success(self, api_client, admin_user, db):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/health/database/")
        data = response.json().get("data")

        assert response.status_code == 200
        assert data["attributes"]["status"] == "ok"
        assert data["attributes"]["db_status"] == "ok"
        assert "db_latency_ms" in data["attributes"]

    def test_database_health_view_database_unavailable(
        self, api_client, admin_user, db, mocker
    ):
        cursor = mocker.MagicMock()
        cursor.__enter__.side_effect = OperationalError()
        mocker.patch("apps.metrics.views.connections")[
            "default"
        ].cursor.return_value = cursor

        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/health/database/")
        data = response.json().get("data")

        assert response.status_code == 200
        assert data["attributes"]["db_status"] == "unavailable"


class TestMetricEventView:
    def test_metric_event_view_permissions(self):
        view = MetricEventView()
        permissions = view.get_permissions()

        assert len(permissions) == 1
        assert isinstance(permissions[0], IsAdmin)

    def test_metric_event_view_get_success(
        self, api_client, admin_user, db, metric_event_factory
    ):
        metric_event_factory.create_batch(size=5)
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/metrics/")
        data = response.json().get("data", [])
        print(data)

        assert response.status_code == 200
        assert len(data) == 5

    def test_metric_event_view_get_summary_success(
        self, api_client, admin_user, db, metric_event_factory
    ):
        metric_event_factory.create_batch(size=5)
        api_client.force_authenticate(user=admin_user)

        response = api_client.get("/metrics/?summary=true")
        data = response.json().get("data", [])
        print(data)

        assert response.status_code == 200


class TestStorageHealthView:
    def test_storage_health_view_permissions(self):
        view = StorageHealthView()
        permissions = view.get_permissions()

        assert len(permissions) == 1
        assert isinstance(permissions[0], IsAdmin)

    def test_storage_health_view_get_success(self, api_client, admin_user, db):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/health/storage/")
        data = response.json().get("data")

        assert response.status_code == 200
        assert data["attributes"]["status"] == "ok"
        assert data["attributes"]["backend"] == "local"
        assert data["attributes"]["reachable"] is True
