from __future__ import absolute_import, unicode_literals

import os
import re
import logging
import tempfile

import gitlab
from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException
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
        pass  # TODO raise exception

    url_components = match.groupdict()

    gl = gitlab.Gitlab(url_components['main_url'], private_token=jmeter_source.token)

    # get project name by id
    project_id = gl.search('projects', url_components['project_name'])[0]['id']

    project = gl.projects.get(project_id)

    temp_dir = tempfile.TemporaryDirectory(prefix='jmeter_sources_')
    logger.info('Temp dir dor script created.', temp_dir.name)

    base_script_filename = os.path.basename(url_components['path'])

    with open(os.path.join(temp_dir.name, base_script_filename), 'wb') as f:
        project.files.raw(file_path=url_components['path'], ref=url_components['branch_name'], action=f.write)

    return temp_dir
    # call this after test stopped
    #temp_dir.cleanup()


def create_k8s_api_instance():
    config.load_kube_config()
    c = Configuration()
    c.assert_hostname = False
    Configuration.set_default(c)
    core_v1 = core_v1_api.CoreV1Api()
    return core_v1


def run_jmeter_master_pod(api_instance, test_id, temp_dir_path):
    name = f'{settings.JMETER_MASTER_POD_PREFIX}-{test_id}'
    resp = None
    try:
        resp = api_instance.read_namespaced_pod(name=name,
                                                namespace='default')
    except ApiException as e:
        if e.status != 404:
            logger.error("Unknown error: %s" % e)

    if not resp:

        logger.info("Pod %s does not exist. Creating it..." % name)
        pod_manifest = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': name
            },
            'spec': {
                'containers': [{
                    'image': 'vmarrazzo/jmeter',
                    'volumeMounts': [{
                        'mountPath': '/mnt/jmeter',
                        'name': 'jmeter-script-volume'
                    }],
                    'name': name,
                    "args": [
                        "-n",
                        "-t /mnt/jmeter/jmeter_debug_test.jmx",
                    ]
                }],
                'restartPolicy': 'Never',
                'volumes': [{
                    'name': 'jmeter-script-volume',
                    'hostPath': {
                        # TODO Перейти на использование скачанного скрипта, когда celery будет запускаться в k8s
                        'path': '/host_mnt/d/jmeter-script-volume',
                        'type': 'DirectoryOrCreate'
                    }
                }]
            }
        }

        resp = api_instance.create_namespaced_pod(body=pod_manifest,
                                                  namespace='default')


@shared_task
def celery_task_start_test(test_id):
    # Скачать скрипт из Гитлаба
    temp_dir = _get_jmeter_source(test_id)

    k8s = create_k8s_api_instance()
    run_jmeter_master_pod(k8s, test_id, temp_dir.name)

    test = Test.objects.get(pk=test_id)
    test.start_time = timezone.now()
    test.save(update_fields=['start_time'])

    # Запустить beat таск, который будет синхронизировать состояние пода из k8s в нашу БД
    from celery import current_app
    app = current_app._get_current_object()
    res = app.add_periodic_task(2.0, celery_task_pull_pod_data.s('Hello'))
    logger.debug('Sync data from k8s scheduled.' + res)


from web.celery import app as celery_app
@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    logger.debug('setup_periodic_tasks')
    sender.add_periodic_task(5.0, celery_task_pull_pod_data.s('hello'))


@celery_app.task
def celery_task_pull_pod_data(*args):
    """
    Задача, которая будет периодически вызываться для подтягивания логов пода из k8s
    :return:
    """
    # TODO Создать отдельную модель OneToOne для запуска пода и сохранения его результатов,
    #    в текущем подходе сохранение теста из любого другого места перётрёт изменения pod_log
    #    Или подтягивать логи напрямую из k8s для отображения, а в БД переносить только при удалении пода
    k8s = create_k8s_api_instance()
    logger.debug('Pulling pod data...')

    for test in Test.objects.filter(state=Test.TestState.RUNNING_JMETER):
        pod_name = f'{settings.JMETER_MASTER_POD_PREFIX}-{test.id}'
        try:
            resp = k8s.read_namespaced_pod(name=pod_name,
                                           namespace='default')
        except ApiException as e:
            if e.status != 404:
                logger.warning("Failed k8s api call", test, e)
            continue
        if resp.status.phase == 'Succeeded':
            api_response = k8s.read_namespaced_pod_log(name=pod_name, namespace='default')
            test.test_completed(api_response)
