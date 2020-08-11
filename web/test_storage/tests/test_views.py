import json
import tempfile

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token

from ..models import Test
from ..models import TestPlan
from ..models import Project
from ..models import LoadStation


class CreateNewJmeterRawLogsFile(TestCase):
    """
    Test module for inserting a new Jmeter Log via REST
    """

    def setUp(self):

        # TODO переписать под обычного пользователя, без привелегий
        user = User.objects.create(username='test_user', is_superuser=True)
        token = Token.objects.create(user=user)
        self.client = Client(HTTP_AUTHORIZATION='Token ' + token.key)

        self.project = Project.objects.create(key='Кей Джей',
                                              name='Тестовый проект',
                                              )

        testplan = TestPlan.objects.create(name='test_plan',
                                           test_type=TestPlan.TestTypes.SMOKE,
                                           project=self.project,
                                           )

        self.load_station = LoadStation.objects.create(hostname='load-station',
                                                       has_horizon_agent=False,
                                                       )

        self.test = Test.objects.create(name='test',
                                        testplan=testplan,
                                        user=user,
                                        )
        self.test.load_stations.set([self.load_station, ])

    def test_create_valid_jmeter_raw_logs_file(self):
        with tempfile.NamedTemporaryFile() as f:

            # file can't be empty
            f.write(b'test')
            f.seek(0)

            form = {
                "file": f,
                "test_id": self.test.id,
            }
            response = self.client.post(
                reverse('test_storage:jmeter-logs'),
                data=form,
            )
            #print(response.content)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_valid_jmeter_raw_logs_file_by_spec_format(self):
        with tempfile.NamedTemporaryFile() as f:
            # file can't be empty
            f.write(b'test2')
            f.seek(0)

            form = {
                "file": f,
                "test_id": 'projectName_20200805_132959',
            }
            response = self.client.post(
                reverse('test_storage:jmeter-logs'),
                data=form,
            )
            result_json = json.loads(response.content)
            # Провекра тайм зон
            self.assertEqual(Test.objects.get(pk=result_json['test_id']).start_time.hour, 9)
            # Проверка создания
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_invalid_puppy(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write(b'test2')
            f.seek(0)
            form = {
                "file": f,
                "test_id": -1,
            }
            response = self.client.post(
                reverse('test_storage:jmeter-logs'),
                data=form,
            )
            print(response.content)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
