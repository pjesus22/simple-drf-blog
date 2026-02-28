from rest_framework import serializers


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    version = serializers.CharField()


class DiagnosticHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.CharField()
    db_latency_ms = serializers.IntegerField()


class EventSummarySerializer(serializers.Serializer):
    event_type = serializers.CharField()
    total = serializers.IntegerField()
    last_7_days = serializers.IntegerField()
    today = serializers.IntegerField()


class StorageHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    backend = serializers.CharField()
    reachable = serializers.BooleanField()
