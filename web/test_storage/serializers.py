from rest_framework import serializers

class TestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    result = serializers.CharField()
    task = serializers.URLField()
    artifacts = serializers.URLField()
    system_version = serializers.CharField()
    rps_avg = serializers.FloatField()
    response_time_avg = serializers.FloatField()
    errors_pct = serializers.FloatField()
    successful = serializers.BooleanField()
    # TODO Добавить testplan, load_stations, user