from django.contrib import admin
from .models import SourceFile,\
    Test,\
    JMRequest,\
    TestPlan,\
    Project,\
    TestPhase,\
    LoadStation

# Register your models here.
admin.site.register(SourceFile)
admin.site.register(Test)
admin.site.register(JMRequest)
admin.site.register(TestPlan)
admin.site.register(Project)
admin.site.register(TestPhase)
admin.site.register(LoadStation)
