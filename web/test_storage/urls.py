from django.urls import path

from .views import TestView
app_name = "test_storage"

# app_name will help us do a reverse look-up latter.
urlpatterns = [
    path('tests/', TestView.as_view()),
]