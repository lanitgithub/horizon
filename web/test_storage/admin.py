from django.contrib import admin
from django.forms import ModelForm

from daterangefilter.filters import PastDateRangeFilter

from .models import JMeterRawLogsFile
from .models import Test
from .models import TestPlan
from .models import Project
from .models import TestPhase
from .models import LoadStation
from .models import Customer


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'customer')


class TestForm(ModelForm):

    class Meta:
        model = Test
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(TestForm, self).__init__(*args, **kwargs)
        instance = self.instance
        if not instance._state.adding:
            if instance and instance.testplan and instance.testplan.project.customer:
                customer = instance.testplan.project.customer
                self.fields['load_stations'].queryset = LoadStation.objects.filter(customer=customer)


class TestAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['name', 'description']}),
        ('Время теста', {'fields': ['start_time', 'end_time']}),
        ('Параметры теста', {'fields': ['testplan', 'load_stations']}),
        ('Результаты теста', {'fields': ['result', 'artifacts', 'rps_avg', 'response_time_avg', 'errors_pct',
                                         'successful']}),
        ('Управление проектом', {'fields': ['task', 'user']}),
    ]
    list_display = ('name', 'start_time', 'end_time', 'testplan', 'user',
                    'rps_avg', 'response_time_avg', 'errors_pct')
    list_filter = ('testplan', 'testplan__project', 'successful', ('start_time', PastDateRangeFilter), ('end_time', PastDateRangeFilter), )
    filter_horizontal = ('load_stations', )
    save_on_top = True
    form = TestForm


class LoadStationAdmin(admin.ModelAdmin):
    list_filter = ('customer', 'customer__project')
    save_on_top = True

# Register your models here.
admin.site.register(Customer)
admin.site.register(JMeterRawLogsFile)
admin.site.register(Test, TestAdmin)
admin.site.register(TestPlan)
admin.site.register(Project, ProjectAdmin)
admin.site.register(TestPhase)
admin.site.register(LoadStation, LoadStationAdmin)
