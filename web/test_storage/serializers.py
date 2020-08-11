import re
import datetime

import pytz
from django.utils import timezone
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ParseError

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
    regex = r"^(.*)_(\d{8}_\d{6})$"
    file = serializers.FileField()
    test_id = serializers.CharField()
    # Строку формата псевдонимпроекта_YYYYMMDD_hhmms вынести в отдельные параметры: project_key, test_start_date

    def create(self, validated_data):
        if not validated_data['test_id'].isdigit():
            # Обработка формата псевдонимпроекта_YYYYMMDD_hhmmss
            # Получить айди теста в БД или создать новый тест
            r = re.search(self.regex, validated_data['test_id'])
            if not r:
                raise ParseError("Can't parse parameter, use this format: 'псевдонимпроекта_YYYYMMDD_hhmmss'")
            project_alias, start_datetime = r.groups()
            start_datetime = datetime.datetime.strptime(start_datetime, '%Y%m%d_%H%M%S')
            start_datetime = pytz.timezone(settings.TIME_ZONE).localize(start_datetime)
            project = Project.objects.get_or_create(key=project_alias,
                                                    defaults={'name': project_alias},
                                                    )[0]
            test_plan = TestPlan.objects.get_or_create(name='Unknown',
                                                       test_type=TestPlan.TestTypes.SMOKE,
                                                       project=project,
                                                       )[0]
            test = Test.objects.get_or_create(name=validated_data['test_id'],
                                              start_time=start_datetime,
                                              testplan=test_plan,
                                              defaults={'end_time': timezone.now(),
                                                        'user': validated_data['user'],
                                                        },
                                              )[0]
            validated_data['test_id'] = test.id

        del validated_data['user']
        return JmeterRawLogsFile.objects.create(**validated_data)