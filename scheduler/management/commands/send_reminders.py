from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from scheduler.models import Reminder, ScheduleConfiguration
from datetime import timedelta, datetime


class Command(BaseCommand):
    help = 'Send due reminders for upcoming appointments'

    def handle(self, *args, **options):
        if not getattr(settings, 'SCHEDULER_EMAIL_ENABLED', False):
            self.stdout.write(self.style.WARNING('Email notifications are disabled in settings'))
            return

        self.stdout.write('Checking for due reminders...')
        
        # Get all unsent reminders that are due
        sent_count = 0
        failed_count = 0
        
        for reminder in Reminder.objects.filter(sent=False):
            if reminder.is_due():
                try:
                    if reminder.send():
                        sent_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Sent reminder for appointment {reminder.appointment.id} '
                                f'({reminder.appointment.client.first_name} {reminder.appointment.client.second_name})'
                            )
                        )
                    else:
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'Failed to send reminder for appointment {reminder.appointment.id}'
                            )
                        )
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'Error sending reminder for appointment {reminder.appointment.id}: {str(e)}'
                        )
                    )
        
        total = sent_count + failed_count
        self.stdout.write(
            self.style.SUCCESS(
                f'Reminder sending complete: {sent_count} sent, {failed_count} failed out of {total} due reminders'
            )
        )
        
        if total == 0:
            self.stdout.write('No due reminders found to send.')