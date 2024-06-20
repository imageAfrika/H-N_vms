from django.contrib import admin
from .models import Visit

class VisitAdmin(admin.ModelAdmin):
    list_display = ['client', 'visit_time']
    search_fields = ('client', 'visit_time')

admin.site.register(Visit, VisitAdmin)
