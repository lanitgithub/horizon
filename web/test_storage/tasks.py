# Create your tasks here
from __future__ import absolute_import, unicode_literals

from celery import shared_task
from .models import Project


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