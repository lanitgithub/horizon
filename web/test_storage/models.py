#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: fileencoding=utf-8

from django.db import models
from django.conf import settings
from datetime import datetime

# TODO: django-adaptors doesn't support python3, switch to https://github.com/edcrewe/django-csvimport
from adaptor.model import CsvModel
from adaptor import fields as csv_fields


class SourceFile(models.Model):
    """Логи jmeter."""
    file = models.FileField(upload_to='source_files/%d.%m.%y')
    test = models.ForeignKey('Test', on_delete=models.CASCADE, blank=True, null=True)

    def __unicode__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        super(SourceFile, self).save(*args, **kwargs)
        JMCsvModel.import_data(data=self.file.file, extra_fields=[{'value': self.pk, 'position': 0}])


class Account(models.Model):
    """
    Аккаунт проекта.
    """
    name = models.CharField('Наименование', max_length=30)
    description = models.TextField('Описание', null=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    # TODO Добавить возможность фильтрации проектов по Аккаунту
    # TODO Добавить возможность фильтрации проектов по владельцу (Свои/Чужие)
    # TODO Добавить возможность разграничения доступа (чтобы тестировщики могли видеть только свои проекты)

    key = models.CharField('Алиас', max_length=10, unique=True, null=False, blank=False)
    name = models.CharField('Наименование', max_length=30)
    account = models.ForeignKey('Account', on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField('Описание', blank=True)

    def __str__(self):
        return f'{self.name} ({self.key})'

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'


class TestPlan(models.Model):
    name = models.CharField('Наименование', max_length=30)
    description_url = models.URLField('Ссылка на описание', blank=True, help_text='wiki')
    documents_url = models.URLField('Документы', blank=True, help_text='Ссылка на sharepoint (МНТ и Отчеты)')
    scripts_url = models.URLField('Ссылка на скрипты', blank=True, help_text='GitLab')
    project = models.ForeignKey('Project', on_delete=models.CASCADE)


class Test(models.Model):
    """
    Итерация тестирования.
    """
    name = models.CharField('Наименование', max_length=30)
    start_time = models.DateTimeField('Дата начала', blank=True)
    end_time = models.DateTimeField('Дата окончания', blank=True)
    result = models.TextField('Краткие результаты', blank=True)
    testplan = models.ForeignKey('TestPlan', on_delete=models.CASCADE, blank=True, null=True)
    task = models.URLField('Задача', blank=True)
    artefacts = models.URLField('Ссылка на артефакты', blank=True)
    load_stations = models.ManyToManyField('LoadStation', verbose_name='Список станций',
                                           help_text='Указываем только станции с которых подавалась нагрузка.')

    # TODO Добавить возможность расширять результаты теста на разных проектах разными артефактами
    #   Например так чтобы можно было добавить ссылки на дефекты производительности, заведенные по результатам теста.

    # TODO Запретить удаление пользователей, иначе тесты удалятся каскадом
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Тест инженер проводивший тест',
    )

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'


class TestPhase(models.Model):
    name = models.CharField('Наименование', max_length=30, help_text='Например, "Рост", "Удержание", "Снижение"')
    start_time = models.DateTimeField('Время начала', blank=True)
    end_time = models.DateTimeField('Время окончания', blank=True)
    testplan = models.ForeignKey('Test', on_delete=models.CASCADE, blank=True)


class LoadStation(models.Model):
    """
    Станции с которых проводился НТ.
    """
    hostname = models.CharField('Hostname', max_length=30)
    has_horizon_agent = models.BooleanField('Является агентом')



class JMRequest(models.Model):
    """Запись запроса в логе. (Одна строка из лога)"""
    source = models.ForeignKey('SourceFile', on_delete=models.CASCADE)
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

    source = csv_fields.DjangoModelField(SourceFile)
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
        dbModel = JMRequest
