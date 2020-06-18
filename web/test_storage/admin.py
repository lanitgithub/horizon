from django.contrib import admin
from .models import RawLogsFile
from .models import Test
from .models import JMRequest
from .models import TestPlan
from .models import Project
from .models import TestPhase
from .models import LoadStation
from .models import Account


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'account')

# Register your models here.
admin.site.register(Account)
admin.site.register(RawLogsFile)
admin.site.register(Test)
admin.site.register(JMRequest)
admin.site.register(TestPlan)
admin.site.register(Project, ProjectAdmin)
admin.site.register(TestPhase)
admin.site.register(LoadStation)
