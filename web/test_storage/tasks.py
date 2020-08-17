from __future__ import absolute_import, unicode_literals

import os
import re
import tempfile

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


def _get_jmeter_source(test_id):
    """
    Скачать из гитлаба исходники (и данные) для запуска теста.
    """
    test = Test.objects.get(id=test_id)
    jmeter_source = test.testplan.jmeter_source
    url = jmeter_source.url

    regex = r'^(?P<main_url>https+:\/\/.+?)\/(?P<group_name>.+?)\/(?P<project_name>.+?)\/-\/blob\/' \
            r'(?P<branch_name>.+?)\/(?P<path>.+\.jmx)$'

    match = re.match(regex, url)

    if not match:
        pass  # TODO raise exception

    url_components = match.groupdict()
    print(url_components)

    gl = gitlab.Gitlab(url_components['main_url'], private_token=jmeter_source.token)

    # get project name by id
    project_id = gl.search('projects', url_components['project_name'])[0]['id']

    project = gl.projects.get(project_id)

    temp_dir = tempfile.TemporaryDirectory(prefix='jmeter_sources_')
    print(temp_dir.name)

    base_script_filename = os.path.basename(url_components['path'])

    with open(os.path.join(temp_dir.name, base_script_filename), 'wb') as f:
        project.files.raw(file_path=url_components['path'], ref=url_components['branch_name'], action=f.write)


    # call this after test stopped
    #temp_dir.cleanup()



@shared_task
def run_jmeter_master(test_id):
    _get_jmeter_source(test_id)
