from rest_framework_json_api import serializers

from apps.metrics.models import MetricRecord


class APIHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    version = serializers.CharField()


class DatabaseHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    version = serializers.CharField()
    db_status = serializers.CharField()
    db_latency_ms = serializers.IntegerField()

    class Meta:
        resource_name = "database-health"


class MetricRecordSummarySerializer(serializers.Serializer):
    id = serializers.CharField(source="event_type")
    event_type = serializers.CharField()
    total = serializers.IntegerField()
    last_7_days = serializers.IntegerField()
    today = serializers.IntegerField()

    class Meta:
        resource_name = "metric-record-summaries"


class MetricRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricRecord
        fields = ("id", "event_type", "metadata", "created_at", "updated_at")
        resource_name = "metric-records"


class StorageHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    backend = serializers.CharField()
    reachable = serializers.BooleanField()
