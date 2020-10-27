#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: fileencoding=utf-8

import os
import _csv
import logging
import shutil
import tempfile
import zipfile
from datetime import datetime

import jmespath
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django_fsm import FSMField, transition


logger = logging.getLogger(__name__)

# TODO: django-adaptors не поддерживает python3, переключиться на использование
#  https://github.com/edcrewe/django-csvimport  <p:0>
try:
    from adaptor.model import CsvModel
    from adaptor import fields as csv_fields
except:
    class CsvModel: pass
    class csv_fields:

        class DateField:
            def __init__(*args, **kwargs): pass

        def IgnoredField(*args, **kwargs): pass
        def DjangoModelField(*args, **kwargs): pass
        def IntegerField(*args, **kwargs): pass
        def CharField(*args, **kwargs): pass
        def BooleanField(*args, **kwargs): pass


class RawLogsFile(models.Model):
    """
    "Сырые", необработанные логи НТ.
    """
    file = models.FileField(upload_to='raw_logs/%d.%m.%y')
    test = models.ForeignKey('Test', on_delete=models.CASCADE)
    # https://stackoverflow.com/questions/1737017/django-auto-now-and-auto-now-add/1737078#1737078
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __unicode__(self):
        return self.file.name

    class Meta:
        abstract = True
        ordering = ['-created_at']
        verbose_name = 'Файл логов НТ'
        verbose_name_plural = 'Файлы логов НТ'


class JmeterRawLogsFile(RawLogsFile):
    """
    Архив с файлом(ами) или файл логов Jmeter.
    """
    def save(self, *args, **kwargs):
        super(RawLogsFile, self).save(*args, **kwargs)
        try:
            JMCsvModel.import_data(data=self.file.file, extra_fields=[{'value': self.pk, 'position': 0}])
        except AttributeError:
            # Загрушка для отстуствующей библиотеки adaptors
            pass
        except _csv.Error:
            # TODO Дописать автоматическое разархивирование JMeterLog <p:0>
            pass

    def __str__(self):
        return self.file.name

    class Meta:
        verbose_name = 'Файлы логов JMeter'
        verbose_name_plural = 'Файлы логов JMeter'


class Customer(models.Model):
    """
    Заказчик проекта. Используется для шруппировки проектов.
    """
    name = models.CharField('Наименование', max_length=30)
    description = models.TextField('Описание', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Заказчик'
        verbose_name_plural = 'Заказчики'


class Project(models.Model):
    # TODO Добавить возможность разграничения доступа (чтобы тестировщики могли видеть только свои проекты) <p:1>
    # TODO Добавить теги ко всем сущностям для сложных пресетов фильтрации <p:1>

    key = models.CharField('Алиас', max_length=20, unique=True, null=False, blank=False)
    name = models.CharField('Наименование', max_length=50)
    customer = models.ForeignKey('test_storage.Customer', verbose_name='Заказчик', on_delete=models.CASCADE, blank=True,
                                 null=True)
    description_url = models.URLField('Ссылка на описание', blank=True, help_text='wiki')

    def __str__(self):
        return f'{self.name} ({self.key})'

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'


class JmeterSource(models.Model):
    url = models.URLField('Ссылка на скрипт в gitlab')
    # TODO Токенами неудобно пользоваться, потому что токен привязан к пользователю и позволяет увидеть всё что доступно пользователю
      # Возможным решением является создание пользователя для CАНТ в гитлаб и генерация токена от этого пользователя. Подумать.
    token = models.CharField('Токен',
                             max_length=30,
                             blank=True,
                             help_text='Токен сгенерировать можно по ссылке: '
                                       'https://gitlab.dks.lanit.ru/profile/personal_access_tokens'
                                       'Необходимые права(scopes): "read_api, read_repository"')

    def __str__(self):
        return self.url

    class Meta:
        verbose_name = 'Скрипт НТ'
        verbose_name_plural = 'Скрипты НТ'


class TestPlan(models.Model):

    name = models.CharField('Наименование', max_length=30)

    # Лучше использовать models.TextChoices в django 3.0 (Аналогичено enum)
    # Типы тестов
    class TestTypes():
        STABLE = 'STB'
        MAX = 'MAX'
        SINTHETIC = 'SIN'
        STRESS = 'STR'
        VOLUME = 'VOL'
        SMOKE = 'SMK'
        SCALABILITY = 'SCA'


        choices = [
            (STABLE, 'Тест стабильности'),
            (MAX, 'Поиск максимума'),
            (SINTHETIC, 'Синтетический тест'),
            (STRESS, 'Стрессовое тестирование'),
            (VOLUME, 'Объемное тестирование'),
            (SMOKE, 'Дымовое тестирование'),
            (SCALABILITY, 'Тестирование масштабируемости'),
        ]

    test_type = models.CharField(
        max_length=3,
        choices=TestTypes.choices,
        default=TestTypes.MAX,
    )

    documents_url = models.URLField('Документы', max_length=1000, blank=True,
                                    help_text='Ссылка на sharepoint (МНТ и Отчеты)')

    jmeter_source = models.ForeignKey('JmeterSource',
                                      blank=True,
                                      null=True,
                                      help_text='GitLab',
                                      on_delete=models.CASCADE,
                                      )
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    description = models.TextField('Описание', blank=True)

    load_stations = models.ManyToManyField('LoadStation', verbose_name='Список станций',
                                           help_text='Указываем только станции с которых ПЛАНИРУЕМ подавать нагрузкау',
                                           )

    # Оставляю закомментированным потому что это может быть лишним, правильнее сразу приучать к STS. Чтобы не усложнять
    # data_pools = models.ManyToManyField('ExternalDataPool', verbose_name='Файл с тестовыми данными',

    def __str__(self):
        return self.name

    def create_test(self, request):

        test = Test(name=self.name,
                    testplan=self,
                    user=request.user,
                    )
        test.save()
        test.load_stations.set(self.load_stations.all())
        test.save()

        return test

    class Meta:
        verbose_name = 'Тест-план'
        verbose_name_plural = 'Тест-планы'


class Test(models.Model):
    """
    Итерация тестирования.
    """

    class TestState(models.TextChoices):
        PREPARE = 'P', _('Подготовка теста инженером')
        RUNNING_JMETER = 'J', _('Running JMeter master')
        COMPLETED = 'C', _('Completed')

    name = models.CharField('Наименование', max_length=100)
    description = models.TextField('Описание', blank=True)
    start_time = models.DateTimeField('Дата начала', blank=True, null=True)
    end_time = models.DateTimeField('Дата окончания', blank=True, null=True)
    result = models.TextField('Краткие результаты', blank=True)
    testplan = models.ForeignKey('TestPlan', on_delete=models.CASCADE)
    task = models.URLField('Задача', blank=True)

    # TODO Remove as Deprecated
    artifacts = models.URLField('DEPRECATED! Ссылка на артефакты', blank=True,
                                help_text='Это поле удалим в следующей ревизии',
                                editable=False,
                                )

    state = FSMField(choices=TestState.choices,
                     default=TestState.PREPARE,
                     )

    # TODO Сделать readonly
    load_stations = models.ManyToManyField('LoadStation', verbose_name='Список станций',
                                           help_text='Указываем только станции с которых ФАКТИЧЕСКИ подавалась нагрузка.',
                                           )
    # TODO Ассёрт на сохранение теста и самих станций (если они привязаны к тесту и с галочкой "Является агентом" без айпшников)

    system_version = models.TextField('Версия системы')

    # TODO Переделать на то чтобы метрики Теста (RPS, Error rate,...) автоматически подтягивались из Фаз теста <p:1>
    rps_avg = models.FloatField('Avg RPS', blank=True, null=True)
    response_time_avg = models.FloatField('Среднее время отклика, сек', blank=True, null=True)
    errors_pct = models.FloatField('% ошибок', blank=True, null=True)
    successful = models.BooleanField('Успешность теста', blank=True, null=True)

    pod_log = models.TextField('Лог автоматического запуска', blank=True)

    # TODO Добавить возможность расширять результаты теста на разных проектах разными артефактами
    #   Например, чтобы можно было добавить ссылки на дефекты производительности, заведенные по
    #   результатам теста. <p:1>

    # TODO Запретить удаление пользователей, иначе тесты удалятся каскадом <p:1>
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Тест инженер проводивший тест',
    )

    def __str__(self):
        return self.name

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name),
                       args=[self.id])

    @transition(field=state, source=[TestState.PREPARE], target=TestState.RUNNING_JMETER)
    def start_test(self):
        from .tasks import celery_task_start_test
        celery_task_start_test.delay(test_id=self.id)

    @transition(field=state, source=[TestState.RUNNING_JMETER], target=TestState.COMPLETED)
    def test_completed(self, log):
        self.state = Test.TestState.COMPLETED
        self.pod_log = log
        self.end_time = timezone.now()
        self.save(update_fields=['state', 'pod_log', 'end_time'])

    # TODO Добавить проверку активности станций перед запуском
    # TODO Добавить проверку агент / не агент
    def _compose_remote_host_arg(self):
        station_ips = [station.ip for station in self.load_stations.all() if station.ip]
        return '-R {0}'.format(','.join(station_ips))

    def get_master_path(self):
        """
        Возвращает путь хостовой ноды, где хранятся скрипт и результаты запуска.
        :return:
        """
        return os.path.join(settings.JMETER_MASTER_DIR, f'{settings.JMETER_MASTER_POD_PREFIX}-{self.id}')

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'


class ExternalLink(models.Model):
    test = models.ForeignKey('Test', on_delete=models.CASCADE)
    url = models.URLField('Ссылка на артефакты', blank=True)
    description = models.TextField('Описание', blank=True)

    # Простой способ скрыть отображение заголовка в Inline форме, если модель ExternalLink приживётся,
    # то переписать на переобредение шаблона
    def __str__(self):
        return ''


#class ExternalDataPool(models.Model):
#    name = models.CharField('Название', blank=True, max_length=128)
#    url = models.URLField('Ссылка на файл с тестовыми данными')

#    def __str__(self):
#        return self.name


class TestPhase(models.Model):
    name = models.CharField('Наименование', max_length=30, help_text='Например, "Рост", "Удержание", "Снижение"')
    # TODO Добавить возможность указания часового пояса <p:1>
    start_time = models.DateTimeField('Время начала', blank=True)
    end_time = models.DateTimeField('Время окончания', blank=True)
    testplan = models.ForeignKey('Test', on_delete=models.CASCADE, blank=True)

    class Meta:
        verbose_name = 'Фаза теста'
        verbose_name_plural = 'Фазы теста'


class LoadStation(models.Model):
    """
    Станции с которых проводился НТ.
    """
    hostname = models.CharField('Hostname', max_length=30)
    has_horizon_agent = models.BooleanField('Является агентом')
    customer = models.ForeignKey('test_storage.Customer', verbose_name='Заказчик', on_delete=models.CASCADE,
                                 blank=True, null=True)
    cpu_count = models.PositiveSmallIntegerField('Количество ядер, штук', null=True, blank=True)
    memory_size = models.FloatField('Объём памяти, Гб', null=True, blank=True)
    disk_size = models.FloatField('Объём диска, Гб', null=True, blank=True)
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    os = models.CharField('Операционная система', max_length=256, null=True, blank=True)
    soft = models.CharField('Программное обеспечение', max_length=256, null=True, blank=True)
    description = models.CharField('Описание', null=True, blank=True, max_length=256)

    class Meta:
        ordering = ['customer', 'hostname']
        verbose_name = 'Нагрузочная станция'
        verbose_name_plural = 'Нагрузочные станции'

    def __str__(self):
        return self.hostname


class JmeterRequest(models.Model):
    """Запись запроса в логе. (Одна строка из лога)"""
    source = models.ForeignKey('JmeterRawLogsFile', on_delete=models.CASCADE)
    timeStamp = models.DateTimeField()
    elapsed = models.PositiveIntegerField()
    label = models.CharField(max_length=255)
    responseCode = models.PositiveSmallIntegerField()
    success = models.BooleanField()
    grpThreads = models.PositiveSmallIntegerField()
    SampleCount = models.PositiveSmallIntegerField()
    ErrorCount = models.PositiveSmallIntegerField()
    Hostname = models.CharField(max_length=30)


class CSVMyDateField(csv_fields.DateField):
    """My DateField class with support unix timestamp format."""

    def to_python(self, value):
        """Add support unix timestamp."""
        if self.format == 'timestamp':
            return datetime.fromtimestamp(float(value))
        else:
            return datetime.strptime(value, self.format)


class JMCsvModel(CsvModel):
    """Сериализация логов JMeter.
        Заголовок лога:
        timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success,failureMessage,bytes,grpThreads,allThreads,URL,Filename,Latency,Encoding,SampleCount,ErrorCount,Hostname,IdleTime
    """

    def ms_to_sec(ms):
        """Convert string in milliseconds to seconds."""
        return '{0}'.format(float(ms) / 1000)

    def digit(value):
        return value if value.isdigit() else 0

    source = csv_fields.DjangoModelField(RawLogsFile)
    timeStamp = CSVMyDateField(format='timestamp', prepare=ms_to_sec)
    elapsed = csv_fields.IntegerField()
    label = csv_fields.CharField()
    responseCode = csv_fields.IntegerField(prepare=digit)
    responseMessage = csv_fields.IgnoredField()
    threadName = csv_fields.IgnoredField()
    dataType = csv_fields.IgnoredField()
    success = csv_fields.BooleanField()
    failureMessage = csv_fields.IgnoredField()
    bytes = csv_fields.IgnoredField()
    grpThreads = csv_fields.IntegerField()
    allThreads = csv_fields.IgnoredField()
    URL = csv_fields.IgnoredField()
    Filename = csv_fields.IgnoredField()
    Latency = csv_fields.IgnoredField()
    Encoding = csv_fields.IgnoredField()
    SampleCount = csv_fields.IntegerField()
    ErrorCount = csv_fields.IntegerField()
    Hostname = csv_fields.CharField()
    IdleTime = csv_fields.IgnoredField()

    class Meta:
        delimiter = ','
        has_header = True
        dbModel = JmeterRequest
