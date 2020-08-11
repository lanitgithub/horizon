from django.urls import path

from .views import TestList, JmeterLogsFileList

# app_name will help us do a reverse look-up latter.
app_name = "test_storage"

urlpatterns = [
    path('tests/', TestList.as_view()),
    path('jmeter_logs/', JmeterLogsFileList.as_view(), name='jmeter-logs'),
]