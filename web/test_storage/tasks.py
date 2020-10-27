from __future__ import absolute_import, unicode_literals

import os
import re
import logging
import subprocess

import gitlab
from celery import shared_task
from django.utils import timezone

from .models import Test
from django.conf import settings


logger = logging.getLogger(__name__)


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
        logger.debug("Can't parse gitlab url %s", url)
        raise Exception("Can't parse gitlab url %s", url)
    else:
        logger.debug("Url parsed. %s", match.groupdict())

    url_components = match.groupdict()

    gl = gitlab.Gitlab(url_components['main_url'], private_token=jmeter_source.token)

    # get project id by name
    # TODO improve it dirty find of project
    projects = gl.search('projects', url_components['project_name'], all=True)
    logger.debug('Found %s projects in gitlab', len(projects))
    path_with_namespace = f"{url_components['group_name']}/{url_components['project_name']}"
    projects = [i for i in projects if i['path_with_namespace'] == path_with_namespace]
    logger.debug('Projects after filter by path_with_namespace :%s.', len(projects))

    # API гитлаба вдруг перестал искать проекты (возвращает только два, а раньше было ~350). Ниже временный костыль
    if len(projects) == 1:
        project_id = projects[0]['id']
    else:
        project_id = 20613228
    # assert len(projects) == 1
    # project_id = projects[0]['id']

    project = gl.projects.get(project_id)

    master_dir = test.get_master_path()
    os.mkdir(master_dir)

    logger.info('Temp dir for jmeter script created: %s', master_dir)

    base_script_filename = os.path.basename(url_components['path'])
    jmx_path = os.path.join(master_dir, base_script_filename)

    with open(jmx_path, 'wb') as f:
        logger.info('Download jmx to %s ', jmx_path)
        project.files.raw(file_path=url_components['path'],
                          ref=url_components['branch_name'],
                          streamed=True,
                          action=f.write)

    return master_dir, base_script_filename


def run_jmeter_master_pod(test_id, temp_dir_path, main_jmx, remote_hosts_arg):
    test = Test.objects.get(pk=test_id)

    cmd = [settings.JMETER_BIN_PATH,
           "-n",
           "-j",
           f"{temp_dir_path}/jmeter.log",
           remote_hosts_arg,
           "-Jserver.rmi.ssl.disable=true",
           "-t",
           f"{temp_dir_path}/{main_jmx}",
           ]
    logger.debug(cmd)
    call_result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    if not call_result.stdout:
        call_result.stdout = ''
    if not call_result.stderr:
        call_result.stderr = ''
    logger.info(call_result.stdout)
    logger.error(call_result.stderr)
    test.test_completed(call_result.stdout + call_result.stderr)


@shared_task
def celery_task_start_test(test_id):
    # Скачать скрипт из Гитлаба
    temp_dir, main_jmx = _get_jmeter_source(test_id)

    test = Test.objects.get(pk=test_id)

    test.start_time = timezone.now()
    test.save(update_fields=['start_time'])

    run_jmeter_master_pod(test_id, temp_dir, main_jmx, test._compose_remote_host_arg())

