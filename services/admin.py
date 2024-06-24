from django.contrib import admin
from .models import Service, Order, OrderItem, Payment

class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'description', 'duration']
    search_fields = ('name', 'price', 'description', 'duration')

admin.site.register(Service, ServiceAdmin)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
