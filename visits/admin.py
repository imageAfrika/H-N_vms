from django.contrib import admin
from .models import Visit

class VisitAdmin(admin.ModelAdmin):
    list_display = ['client', 'date']
    search_fields = ('client', 'date')

admin.site.register(Visit, VisitAdmin)
