from rest_framework import serializers as drf_serializers
from rest_framework_json_api import serializers as json_api_serializers

from apps.metrics.models import MetricEvent


class HealthSerializer(drf_serializers.Serializer):
    status = drf_serializers.CharField()
    version = drf_serializers.CharField()


class DiagnosticHealthSerializer(drf_serializers.Serializer):
    status = drf_serializers.CharField()
    database = drf_serializers.CharField()
    db_latency_ms = drf_serializers.IntegerField()


class MetricEventSummarySerializer(json_api_serializers.Serializer):
    id = drf_serializers.CharField(source="event_type")
    event_type = drf_serializers.CharField()
    total = drf_serializers.IntegerField()
    last_7_days = drf_serializers.IntegerField()
    today = drf_serializers.IntegerField()

    class Meta:
        resource_name = "metric-event-summaries"


class MetricEventSerializer(json_api_serializers.ModelSerializer):
    class Meta:
        model = MetricEvent
        fields = (
            "id",
            "event_type",
            "user",
            "metadata",
            "created_at",
        )


class StorageHealthSerializer(drf_serializers.Serializer):
    status = drf_serializers.CharField()
    backend = drf_serializers.CharField()
    reachable = drf_serializers.BooleanField()
