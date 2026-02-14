from rest_framework import serializers


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    version = serializers.CharField()


class DiagnosticHealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.CharField()
    db_latency_ms = serializers.IntegerField()
