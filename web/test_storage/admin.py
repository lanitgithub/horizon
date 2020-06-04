from django.contrib import admin
from test_storage.models import SourceFile, Test, JMRequest

# Register your models here.
admin.site.register(SourceFile)
admin.site.register(Test)
admin.site.register(JMRequest)