from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from users.models import Client
from services.models import Service
import icalendar
from datetime import timedelta, datetime


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    duration = models.DurationField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    reminder_sent = models.BooleanField(default=False)
    reminder_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['date', 'time']),
            models.Index(fields=['status']),
            models.Index(fields=['client']),
        ]
    
    def __str__(self):
        return f"{self.client.first_name} {self.client.second_name} - {self.service.name} on {self.date} at {self.time}"
    
    def get_end_time(self):
        """Calculate end time based on duration or service duration"""
        if self.duration:
            duration = self.duration
        elif self.service.duration:
            duration = self.service.duration
        else:
            duration = timedelta(hours=1)  # Default 1 hour
        
        start_datetime = timezone.make_aware(datetime.combine(self.date, self.time))
        return (start_datetime + duration).time()
    
    def to_ical(self):
        """Convert appointment to iCalendar format for Thunderbird sync"""
        cal = icalendar.Calendar()
        cal.add('prodid', '-//H-N VMS Scheduler//mxm.dk//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        
        event = icalendar.Event()
        event.add('summary', f"{self.service.name} - {self.client.first_name} {self.client.second_name}")
        event.add('dtstart', timezone.make_aware(datetime.combine(self.date, self.time)))
        
        end_time = self.get_end_time()
        event.add('dtend', timezone.make_aware(datetime.combine(self.date, end_time)))
        
        if self.notes:
            event.add('description', self.notes)
        
        # Add client contact information
        event.add('organizer', f"mailto:{self.client.email}")
        event.add('attendee', f"mailto:{self.client.email}", cn=f"{self.client.first_name} {self.client.second_name}")
        
        # Add status based on appointment status
        status_map = {
            'scheduled': 'TENTATIVE',
            'confirmed': 'CONFIRMED',
            'completed': 'CONFIRMED',
            'cancelled': 'CANCELLED',
            'no_show': 'CANCELLED'
        }
        event.add('status', status_map.get(self.status, 'TENTATIVE'))
        
        event.add('dtstamp', self.created_at)
        event['uid'] = f"appointment-{self.id}@hn-vms.local"
        event['sequence'] = 0
        
        cal.add_component(event)
        return cal.to_ical()
    
    def check_conflicts(self):
        """Check for conflicting appointments"""
        start_datetime = timezone.make_aware(datetime.combine(self.date, self.time))
        end_time = self.get_end_time()
        end_datetime = timezone.make_aware(datetime.combine(self.date, end_time))
        
        conflicts = Appointment.objects.filter(
            date=self.date,
            status__in=['scheduled', 'confirmed']
        ).exclude(id=self.id)
        
        for appointment in conflicts:
            apt_start = timezone.make_aware(datetime.combine(appointment.date, appointment.time))
            apt_end = timezone.make_aware(datetime.combine(appointment.date, appointment.get_end_time()))
            
            if (start_datetime < apt_end) and (end_datetime > apt_start):
                return True, appointment
        
        return False, None


class Message(models.Model):
    MESSAGE_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App'),
        ('notification', 'Notification'),
    ]
    
    DIRECTION_CHOICES = [
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='outgoing')
    subject = models.CharField(max_length=200, blank=True, null=True)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['status']),
            models.Index(fields=['message_type']),
        ]
    
    def __str__(self):
        return f"{self.get_message_type_display()} - {self.subject or 'No subject'}"
    
    def send(self):
        """Send the message based on type"""
        if self.message_type == 'email' and self.client:
            try:
                send_mail(
                    subject=self.subject,
                    message=self.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[self.client.email],
                    fail_silently=False,
                )
                self.status = 'sent'
                self.sent_at = timezone.now()
                self.save()
                return True
            except Exception as e:
                self.status = 'failed'
                self.save()
                return False
        return False


class EmailTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def render(self, context):
        """Render template with given context"""
        try:
            subject = render_to_string('', context, subject=self.subject)
            body = render_to_string('', context, body=self.body)
            return subject, body
        except Exception:
            return self.subject, self.body


class Reminder(models.Model):
    REMINDER_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES, default='email')
    remind_before = models.DurationField()  # How long before appointment to remind
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['appointment', 'remind_before']
        unique_together = ['appointment', 'reminder_type', 'remind_before']
    
    def __str__(self):
        return f"{self.get_reminder_type_display()} reminder for {self.appointment}"
    
    def is_due(self):
        """Check if reminder is due to be sent"""
        appointment_datetime = timezone.make_aware(
            datetime.combine(self.appointment.date, self.appointment.time)
        )
        reminder_time = appointment_datetime - self.remind_before
        return timezone.now() >= reminder_time and not self.sent
    
    def send(self):
        """Send the reminder"""
        if self.reminder_type == 'email' and self.appointment.client:
            subject = f"Reminder: {self.appointment.service.name} appointment"
            message = f"""
Dear {self.appointment.client.first_name},

This is a reminder that you have an appointment for {self.appointment.service.name}
scheduled on {self.appointment.date} at {self.appointment.time}.

Please arrive 10 minutes early.

If you need to reschedule, please contact us.
            """
            
            try:
                send_mail(
                    subject=subject,
                    message=message.strip(),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[self.appointment.client.email],
                    fail_silently=False,
                )
                self.sent = True
                self.sent_at = timezone.now()
                self.save()
                
                # Update appointment reminder status
                self.appointment.reminder_sent = True
                self.appointment.reminder_time = timezone.now()
                self.appointment.save()
                
                return True
            except Exception as e:
                return False
        return False


class ScheduleConfiguration(models.Model):
    """Store configuration for scheduling system"""
    business_name = models.CharField(max_length=200, default='H-N VMS')
    business_email = models.EmailField(default='info@hn-vms.com')
    business_phone = models.CharField(max_length=20, blank=True, null=True)
    default_appointment_duration = models.DurationField(default=timedelta(hours=1))
    advance_booking_days = models.IntegerField(default=30)
    cancellation_hours = models.IntegerField(default=24)
    reminder_default_hours = models.IntegerField(default=24)
    enable_caldav = models.BooleanField(default=False)
    caldav_url = models.URLField(blank=True, null=True)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    
    def __str__(self):
        return f"Schedule Configuration for {self.business_name}"
    
    @classmethod
    def get_config(cls):
        """Get or create default configuration"""
        config, created = cls.objects.get_or_create(id=1)
        return config
