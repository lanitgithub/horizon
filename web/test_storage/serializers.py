import datetime
from rest_framework import serializers

from .models import JmeterRawLogsFile
from .models import Project
from .models import Test
from .models import TestPlan


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


class JmeterRawLogsFileSerializer(serializers.Serializer):
    file = serializers.FileField()
    test_id = serializers.CharField()

    def create(self, validated_data):
        if not validated_data['test_id'].isdigit():
            # Обработка формата псевдонимпроекта_YYYYMMDD_hhmmss
            # Получить айди теста в БД или создать новый тест
            project_alias, start_datetime = validated_data['test_id'].split('_', maxsplit=1)
            start_datetime = datetime.datetime.strptime(start_datetime, '%Y%m%d_%H%M%S')
            project = Project.objects.get_or_create(key=project_alias,
                                                    defaults={'name': project_alias},
                                                    )[0]
            test_plan = TestPlan.objects.get_or_create(name='Unknown',
                                                       test_type=TestPlan.TestTypes.SMOKE,
                                                       project=project,
                                                       )[0]
            test = Test.objects.get_or_create(name=test_plan.name,
                                              start_time=start_datetime,
                                              testplan=test_plan,
                                              defaults={'end_time': datetime.datetime.now(),
                                                        'user': validated_data['user'],
                                                        },
                                              )[0]
            validated_data['test_id'] = test.id

        del validated_data['user']
        return JmeterRawLogsFile.objects.create(**validated_data)