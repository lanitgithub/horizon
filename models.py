#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: fileencoding=utf-8

from django.db import models
from datetime import datetime

from adaptor.model import CsvModel
from adaptor import fields as csv_fields


class SourceFile(models.Model):
    '''Логи jmeter.'''
    file = models.FileField(upload_to='source_files/%d.%m.%y')
    test = models.ForeignKey('Test', blank=True, null=True)

    def __unicode__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        super(SourceFile, self).save(*args, **kwargs)
        JMCsvModel.import_data(data=self.file.file, extra_fields=[{'value': self.pk, 'position': 0}])


class Test(models.Model):
    '''Итерация тестирования.'''

    name = models.CharField(max_length=30)
    start_time = models.DateTimeField(blank=True)
    end_time = models.DateTimeField(blank=True)


class JMRequest(models.Model):
    '''Запись запроса в логе. (Одна строка из лога)'''
    source = models.ForeignKey('SourceFile')
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
    '''My DateField class with support unix timestamp format.'''

    def to_python(self, value):
        '''Add support unix timestamp.'''
        if self.format == 'timestamp':
            return datetime.fromtimestamp(float(value))
        else:
            return datetime.strptime(value, self.format)


class JMCsvModel(CsvModel):
    '''Сериализация логов JMeter.
        Заголовок лога:
        timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success,failureMessage,bytes,grpThreads,allThreads,URL,Filename,Latency,Encoding,SampleCount,ErrorCount,Hostname,IdleTime
    '''

    def ms_to_sec(ms):
        '''Convert string in milliseconds to seconds.'''
        return '{0}'.format(float(ms)/1000)

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


