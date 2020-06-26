from django.urls import path

from .views import TestList, JmeterLogsFileList

app_name = "test_storage"

# app_name will help us do a reverse look-up latter.
urlpatterns = [
    path('tests/', TestList.as_view()),
    path('jmeter_logs/', JmeterLogsFileList.as_view()),
]