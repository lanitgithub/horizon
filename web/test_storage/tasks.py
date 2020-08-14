# Create your tasks here
from __future__ import absolute_import, unicode_literals

import gitlab
from celery import shared_task

from .models import Project
from .models import Test


@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y


@shared_task
def xsum(numbers):
    return sum(numbers)


@shared_task
def count_projects():
    return Project.objects.count()


@shared_task
def rename_Project(project_id, name):
    w = Project.objects.get(id=project_id)
    w.name = name
    w.save()


def _get_jmeter_source(test_id, name):
    """
    Скачать из гитлаба исходники (и данные) для запуска теста.
    """
    test = Test.objects.get(id=test_id)
    jmeter_source = test.testplan.jmeter_source
    gl = gitlab.Gitlab('https://gitlab.dks.lanit.ru', private_token=jmeter_source.token)
    gitlab.v4.objects.ProjectFileManager(gl, ref='master')



@shared_task
def run_jmeter_master(test_id):
    _get_jmeter_source(test_id)
