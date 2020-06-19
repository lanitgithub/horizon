from django.contrib import admin
from .models import JMeterRawLogsFile
from .models import Test
from .models import TestPlan
from .models import Project
from .models import TestPhase
from .models import LoadStation
from .models import Account


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'account')


class TestAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['name', 'description']}),
        ('Время теста', {'fields': ['start_time', 'end_time']}),
        ('Параметры теста', {'fields': ['testplan', 'load_stations']}),
        ('Результаты теста', {'fields': ['result', 'artifacts', 'rps_avg', 'response_time_avg', 'errors_pct',
                                         'successful']}),
        ('Управление проектом', {'fields': ['task', 'user']}),
    ]
    save_on_top = True

# Register your models here.
admin.site.register(Account)
admin.site.register(JMeterRawLogsFile)
admin.site.register(Test, TestAdmin)
admin.site.register(TestPlan)
admin.site.register(Project, ProjectAdmin)
admin.site.register(TestPhase)
admin.site.register(LoadStation)
