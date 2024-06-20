from django.contrib import admin
from .models import Client, Referral

class ClientAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'second_name', 'email', 'phone',
                    'points', 'referral_points', 'referred_by', 'card_paid', 'card_issued']
    search_fields = ('first_name', 'second_name', 'phone')
    ordering = ['id']

class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referred_client', 'date']
    search_fields = ('referrer', 'referred_client')

admin.site.register(Client, ClientAdmin)
admin.site.register(Referral, ReferralAdmin)
