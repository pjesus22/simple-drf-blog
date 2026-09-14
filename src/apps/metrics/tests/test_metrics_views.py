import warnings

from django.core.paginator import UnorderedObjectListWarning
from django.db.utils import OperationalError
import pytest
from rest_framework.permissions import AllowAny
from rest_framework.test import APIClient

from apps.accounts.permissions import IsAdmin
from apps.metrics.views import (
    APIHealthView,
    DatabaseHealthView,
    MetricRecordView,
    StorageHealthView,
)
from config.throttle import UserReadThrottle


@pytest.fixture
def api_client():
    return APIClient()


def test_metrics_views_return_correct_throttle_for_action():
    assert APIHealthView.throttle_classes == []
    assert DatabaseHealthView.throttle_classes == [UserReadThrottle]
    assert StorageHealthView.throttle_classes == [UserReadThrottle]
    assert MetricRecordView.throttle_classes == [UserReadThrottle]


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

    def test_database_health_view_get_success(self, api_client, admin_factory, db):
        api_client.force_authenticate(user=admin_factory())
        response = api_client.get("/health/database/")
        data = response.json().get("data")

        assert response.status_code == 200
        assert data["attributes"]["status"] == "ok"
        assert data["attributes"]["db_status"] == "ok"
        assert "db_latency_ms" in data["attributes"]

    def test_database_health_view_database_unavailable(
        self, api_client, admin_factory, db, mocker
    ):
        cursor = mocker.MagicMock()
        cursor.__enter__.side_effect = OperationalError()
        mocker.patch("apps.metrics.views.connections")[
            "default"
        ].cursor.return_value = cursor

        api_client.force_authenticate(user=admin_factory())
        response = api_client.get("/health/database/")
        data = response.json().get("data")

        assert response.status_code == 200
        assert data["attributes"]["db_status"] == "unavailable"


class TestMetricRecordView:
    def test_metric_event_view_permissions(self):
        view = MetricRecordView()
        permissions = view.get_permissions()

        assert len(permissions) == 1
        assert isinstance(permissions[0], IsAdmin)

    def test_metric_event_view_get_success(
        self, api_client, admin_factory, db, metric_record_factory
    ):
        metric_record_factory.create_batch(size=5)
        api_client.force_authenticate(user=admin_factory())

        response = api_client.get("/metrics/")
        data = response.json().get("data", [])

        assert response.status_code == 200
        assert len(data) == 5

    def test_metric_event_view_get_summary_success(
        self, api_client, admin_factory, db, metric_record_factory
    ):
        metric_record_factory.create_batch(size=5)
        api_client.force_authenticate(user=admin_factory())

        response = api_client.get("/metrics/?summary=true")

        assert response.status_code == 200

    def test_metric_event_view_default_page(
        self, api_client, admin_factory, db, metric_record_factory
    ):
        metric_record_factory.create_batch(size=12)
        api_client.force_authenticate(user=admin_factory())

        response = api_client.get("/metrics/")
        body = response.json()

        assert response.status_code == 200
        assert len(body["data"]) == 10
        assert body["meta"]["pagination"] == {"page": 1, "pages": 2, "count": 12}
        assert body["links"]["first"].endswith("/metrics/?page%5Bnumber%5D=1")
        assert body["links"]["last"].endswith("/metrics/?page%5Bnumber%5D=2")
        assert body["links"]["next"].endswith("/metrics/?page%5Bnumber%5D=2")
        assert body["links"]["prev"] is None

    def test_metric_event_view_second_page(
        self, api_client, admin_factory, db, metric_record_factory
    ):
        metric_record_factory.create_batch(size=12)
        api_client.force_authenticate(user=admin_factory())

        response = api_client.get("/metrics/?page[number]=2")
        body = response.json()

        assert response.status_code == 200
        assert len(body["data"]) == 2
        assert body["meta"]["pagination"]["page"] == 2
        assert body["links"]["next"] is None
        assert body["links"]["prev"].endswith("/metrics/?page%5Bnumber%5D=1")

    def test_metric_event_view_page_size_and_cap(
        self, api_client, admin_factory, db, metric_record_factory
    ):
        metric_record_factory.create_batch(size=120)
        api_client.force_authenticate(user=admin_factory())

        assert len(api_client.get("/metrics/?page[size]=5").json()["data"]) == 5
        assert len(api_client.get("/metrics/?page[size]=500").json()["data"]) == 100

    def test_metric_event_view_does_not_warn_on_unordered_queryset(
        self, api_client, admin_factory, db, metric_record_factory
    ):
        metric_record_factory.create_batch(12)
        api_client.force_authenticate(user=admin_factory())

        with warnings.catch_warnings():
            warnings.simplefilter("error", UnorderedObjectListWarning)
            response = api_client.get("/metrics/")

        assert response.status_code == 200

    def test_metric_event_view_summary_is_paginated(
        self, api_client, admin_factory, db, metric_record_factory
    ):
        metric_record_factory.create_batch(size=12, event_type="page_view")
        api_client.force_authenticate(user=admin_factory())

        response = api_client.get("/metrics/?summary=true")
        body = response.json()

        assert response.status_code == 200
        assert len(body["data"]) == 1
        assert body["meta"]["pagination"]["count"] == 1
        assert body["data"][0]["attributes"]["event_type"] == "page_view"


class TestStorageHealthView:
    def test_storage_health_view_permissions(self):
        view = StorageHealthView()
        permissions = view.get_permissions()

        assert len(permissions) == 1
        assert isinstance(permissions[0], IsAdmin)

    def test_storage_health_view_get_success(self, api_client, admin_factory, db):
        api_client.force_authenticate(user=admin_factory())
        response = api_client.get("/health/storage/")
        data = response.json().get("data")

        assert response.status_code == 200
        assert data["attributes"]["status"] == "ok"
        assert data["attributes"]["reachable"] is True
