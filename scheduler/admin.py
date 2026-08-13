from django.contrib import admin
from django.utils import timezone
from .models import Appointment, Message, EmailTemplate, Reminder, ScheduleConfiguration
from django.http import HttpResponse
import datetime


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['client', 'service', 'date', 'time', 'status', 'priority', 'reminder_sent']
    list_filter = ['status', 'priority', 'date', 'service']
    search_fields = ['client__first_name', 'client__second_name', 'client__email', 'service__name', 'notes']
    date_hierarchy = 'date'
    ordering = ['date', 'time']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('client', 'service', 'date', 'time', 'duration')
        }),
        ('Additional Information', {
            'fields': ('notes', 'status', 'priority')
        }),
        ('Reminder Information', {
            'fields': ('reminder_sent', 'reminder_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['send_reminders', 'mark_as_confirmed', 'mark_as_completed', 'export_ical']
    
    def send_reminders(self, request, queryset):
        sent_count = 0
        for appointment in queryset:
            # Create and send reminder
            from datetime import timedelta
            reminder, created = Reminder.objects.get_or_create(
                appointment=appointment,
                reminder_type='email',
                remind_before=timedelta(hours=24),
                defaults={'sent': False}
            )
            if reminder.send():
                sent_count += 1
        
        self.message_user(request, f'{sent_count} reminders sent successfully.')
    send_reminders.short_description = 'Send reminders for selected appointments'
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} appointments marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark selected as confirmed'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} appointments marked as completed.')
    mark_as_completed.short_description = 'Mark selected as completed'
    
    def export_ical(self, request, queryset):
        """Export selected appointments as iCalendar file"""
        import icalendar
        
        cal = icalendar.Calendar()
        cal.add('prodid', '-//H-N VMS Scheduler//mxm.dk//')
        cal.add('version', '2.0')
        
        for appointment in queryset:
            cal.add_component(icalendar.Event.from_ical(appointment.to_ical().decode('utf-8')))
        
        response = HttpResponse(cal.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename=appointments.ics'
        return response
    export_ical.short_description = 'Export selected as iCalendar'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['client', 'message_type', 'direction', 'subject', 'status', 'created_at']
    list_filter = ['message_type', 'direction', 'status', 'created_at']
    search_fields = ['client__first_name', 'client__second_name', 'subject', 'body']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'delivered_at', 'read_at']
    
    fieldsets = (
        ('Message Details', {
            'fields': ('client', 'message_type', 'direction', 'subject', 'body')
        }),
        ('Status Information', {
            'fields': ('status', 'appointment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at', 'delivered_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['send_messages']
    
    def send_messages(self, request, queryset):
        sent_count = 0
        for message in queryset.filter(status='draft'):
            if message.send():
                sent_count += 1
        
        self.message_user(request, f'{sent_count} messages sent successfully.')
    send_messages.short_description = 'Send selected draft messages'


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'subject', 'body']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Template Details', {
            'fields': ('name', 'subject', 'body', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'reminder_type', 'remind_before', 'sent', 'sent_at']
    list_filter = ['reminder_type', 'sent', 'sent_at']
    search_fields = ['appointment__client__first_name', 'appointment__client__second_name']
    readonly_fields = ['created_at', 'sent_at']
    
    fieldsets = (
        ('Reminder Details', {
            'fields': ('appointment', 'reminder_type', 'remind_before')
        }),
        ('Status', {
            'fields': ('sent', 'sent_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['send_due_reminders']
    
    def send_due_reminders(self, request, queryset):
        sent_count = 0
        for reminder in queryset:
            if reminder.is_due() and reminder.send():
                sent_count += 1
        
        self.message_user(request, f'{sent_count} due reminders sent successfully.')
    send_due_reminders.short_description = 'Send due reminders'


@admin.register(ScheduleConfiguration)
class ScheduleConfigurationAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'business_email', 'enable_caldav', 'timezone']
    readonly_fields = []
    
    fieldsets = (
        ('Business Information', {
            'fields': ('business_name', 'business_email', 'business_phone')
        }),
        ('Scheduling Settings', {
            'fields': ('default_appointment_duration', 'advance_booking_days', 'cancellation_hours', 'reminder_default_hours')
        }),
        ('CalDAV Settings', {
            'fields': ('enable_caldav', 'caldav_url')
        }),
        ('System Settings', {
            'fields': ('timezone',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one configuration instance
        return not ScheduleConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the configuration
        return False
