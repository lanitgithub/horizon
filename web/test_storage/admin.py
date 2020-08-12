from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from daterangefilter.filters import PastDateRangeFilter

from .models import JmeterRawLogsFile
from .models import Test
from .models import JmeterSource
from .models import TestPlan
from .models import Project
from .models import TestPhase
from .models import LoadStation
from .models import Customer
from .models import ExternalLink


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'customer')
    list_filter = ('customer',)


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


class ExternalLinkInline(admin.TabularInline):
    model = ExternalLink
    extra = 1


class TestAdmin(admin.ModelAdmin):
    inlines = [
        ExternalLinkInline,
    ]
    fieldsets = [
        (None, {'fields': ['name', 'description']}),
        ('Время теста', {'fields': ['start_time', 'end_time', 'state']}),
        ('Параметры теста', {'fields': ['testplan', 'load_stations']}),
        ('Результаты теста', {'fields': ['result', 'rps_avg', 'response_time_avg', 'errors_pct',
                                         'successful']}),
        ('Управление проектом', {'fields': ['task', 'user']}),
    ]
    list_display = ('name', 'start_time', 'end_time', 'testplan', 'user_label',
                    'rps_avg', 'response_time_avg', 'errors_pct')
    list_filter = ('testplan', 'testplan__project', 'successful', ('start_time', PastDateRangeFilter),
                   ('end_time', PastDateRangeFilter), 'user')
    filter_horizontal = ('load_stations',)
    save_on_top = True
    form = TestForm

    def user_label(self, obj):
        if obj.user.first_name or obj.user.last_name:
            return "{0} {1}".format(obj.user.first_name, obj.user.last_name)
        else:
            return obj.user.username


class TestPlanAdmin(admin.ModelAdmin):

    change_form_template = 'admin/test_storage/test_plan/change_form.html'

    list_display = ('name', 'project', 'test_type')
    list_filter = ('project', )
    save_on_top = True

    def response_change(self, request, obj):
        res = super().response_change(request, obj)
        if "_run-test" in request.POST:
            test = obj.run_test(request)
            self.message_user(request, 'Test ran.')
            return HttpResponseRedirect(test.get_admin_url())
        return res


class LoadStationAdmin(admin.ModelAdmin):
    list_filter = ('customer', )
    list_display = ('hostname', 'description', )
    save_on_top = True


class JmeterRawLogsFileAdmin(admin.ModelAdmin):
    list_display = ('test', 'created_at', 'updated_at')


# Register your models here.
admin.site.register(Customer)
admin.site.register(JmeterRawLogsFile, JmeterRawLogsFileAdmin)
admin.site.register(Test, TestAdmin)
admin.site.register(TestPlan, TestPlanAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(TestPhase)
admin.site.register(JmeterSource)
admin.site.register(LoadStation, LoadStationAdmin)
