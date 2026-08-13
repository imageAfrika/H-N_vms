from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from calendar import monthcalendar
from datetime import datetime, timedelta
from .models import Appointment, Message, Reminder, ScheduleConfiguration
from users.models import Client
from services.models import Service
from django import forms


# Forms
class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['client', 'service', 'date', 'time', 'duration', 'notes', 'priority']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['client', 'message_type', 'subject', 'body', 'appointment']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
        }

class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ['appointment', 'reminder_type', 'remind_before']
        widgets = {
            'remind_before': forms.Select(choices=[
                (timedelta(hours=1), '1 hour before'),
                (timedelta(hours=24), '1 day before'),
                (timedelta(hours=48), '2 days before'),
                (timedelta(days=7), '1 week before'),
            ]),
        }


# Dashboard
@login_required
def scheduler_dashboard(request):
    """Main scheduler dashboard"""
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    week_end = today + timedelta(days=7)
    
    # Today's appointments
    today_appointments = Appointment.objects.filter(
        date=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('time')
    
    # Upcoming appointments this week
    upcoming_appointments = Appointment.objects.filter(
        date__gt=today,
        date__lte=week_end,
        status__in=['scheduled', 'confirmed']
    ).order_by('date', 'time')
    
    # Recent messages
    recent_messages = Message.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-created_at')[:10]
    
    # Pending reminders
    pending_reminders = Reminder.objects.filter(sent=False).count()
    
    # Statistics
    total_appointments = Appointment.objects.filter(date__month=today.month).count()
    completed_today = Appointment.objects.filter(date=today, status='completed').count()
    
    context = {
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'recent_messages': recent_messages,
        'pending_reminders': pending_reminders,
        'total_appointments': total_appointments,
        'completed_today': completed_today,
        'today': today,
    }
    return render(request, 'scheduler/dashboard.html', context)


# Calendar Views
@login_required
def calendar_view(request, year=None, month=None):
    """Calendar view with monthly overview"""
    today = timezone.now().date()
    
    if year and month:
        current_date = datetime(year, month, 1).date()
    else:
        current_date = today
    
    # Get calendar data
    cal_data = monthcalendar(current_date.year, current_date.month)
    
    # Get appointments for the month
    month_start = datetime(current_date.year, current_date.month, 1).date()
    if current_date.month == 12:
        month_end = datetime(current_date.year + 1, 1, 1).date() - timedelta(days=1)
    else:
        month_end = datetime(current_date.year, current_date.month + 1, 1).date() - timedelta(days=1)
    
    appointments = Appointment.objects.filter(
        date__range=[month_start, month_end],
        status__in=['scheduled', 'confirmed']
    ).order_by('date', 'time')
    
    # Navigation
    prev_month = current_date - timedelta(days=32)
    prev_month = prev_month.replace(day=1)
    next_month = current_date + timedelta(days=32)
    next_month = next_month.replace(day=1)
    
    context = {
        'year': current_date.year,
        'month': current_date.month,
        'month_name': current_date.strftime('%B %Y'),
        'cal_data': cal_data,
        'appointments': appointments,
        'prev_month': prev_month,
        'next_month': next_month,
        'today': today,
        'calendar_appointments': appointments,  # Alternative name for template compatibility
    }
    return render(request, 'scheduler/calendar.html', context)


# Appointment Views
@login_required
def appointment_list(request):
    """List all appointments with filtering"""
    appointments = Appointment.objects.all().order_by('-date', '-time')
    
    # Filtering
    status_filter = request.GET.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    date_filter = request.GET.get('date')
    if date_filter:
        appointments = appointments.filter(date=date_filter)
    
    search_query = request.GET.get('search')
    if search_query:
        appointments = appointments.filter(
            Q(client__first_name__icontains=search_query) |
            Q(client__second_name__icontains=search_query) |
            Q(service__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(appointments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search_query': search_query,
    }
    return render(request, 'scheduler/appointment_list.html', context)


@login_required
def appointment_create(request):
    """Create a new appointment"""
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            
            # Check for conflicts
            has_conflict, conflicting_appointment = appointment.check_conflicts()
            if has_conflict:
                form.add_error(None, f'Time conflict with existing appointment: {conflicting_appointment}')
                return render(request, 'scheduler/appointment_form.html', {'form': form, 'mode': 'create'})
            
            appointment.save()
            
            # Create default reminder
            config = ScheduleConfiguration.get_config()
            default_reminder_hours = config.reminder_default_hours
            Reminder.objects.create(
                appointment=appointment,
                reminder_type='email',
                remind_before=timedelta(hours=default_reminder_hours)
            )
            
            return redirect('scheduler:appointment_detail', pk=appointment.id)
    else:
        form = AppointmentForm()
    
    return render(request, 'scheduler/appointment_form.html', {'form': form, 'mode': 'create'})


@login_required
def appointment_detail(request, pk):
    """View appointment details"""
    appointment = get_object_or_404(Appointment, pk=pk)
    reminders = appointment.reminders.all()
    messages = appointment.messages.all()
    
    context = {
        'appointment': appointment,
        'reminders': reminders,
        'messages': messages,
    }
    return render(request, 'scheduler/appointment_detail.html', context)


@login_required
def appointment_update(request, pk):
    """Update an existing appointment"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            updated_appointment = form.save(commit=False)
            
            # Check for conflicts (excluding current appointment)
            has_conflict, conflicting_appointment = updated_appointment.check_conflicts()
            if has_conflict:
                form.add_error(None, f'Time conflict with existing appointment: {conflicting_appointment}')
                return render(request, 'scheduler/appointment_form.html', {'form': form, 'mode': 'update', 'appointment': appointment})
            
            updated_appointment.save()
            return redirect('scheduler:appointment_detail', pk=appointment.id)
    else:
        form = AppointmentForm(instance=appointment)
    
    return render(request, 'scheduler/appointment_form.html', {'form': form, 'mode': 'update', 'appointment': appointment})


@login_required
def appointment_delete(request, pk):
    """Delete an appointment"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.method == 'POST':
        appointment.delete()
        return redirect('scheduler:appointment_list')
    
    return render(request, 'scheduler/appointment_confirm_delete.html', {'appointment': appointment})


@login_required
def appointment_confirm(request, pk):
    """Confirm an appointment"""
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = 'confirmed'
    appointment.save()
    
    # Send confirmation message
    if appointment.client.email:
        Message.objects.create(
            client=appointment.client,
            message_type='email',
            subject=f'Appointment Confirmed: {appointment.service.name}',
            body=f'Dear {appointment.client.first_name},\n\nYour appointment for {appointment.service.name} on {appointment.date} at {appointment.time} has been confirmed.\n\nPlease arrive 10 minutes early.',
            direction='outgoing',
            appointment=appointment,
            status='draft'
        )
    
    return redirect('scheduler:appointment_detail', pk=appointment.id)


@login_required
def appointment_cancel(request, pk):
    """Cancel an appointment"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        
        # Send cancellation message
        if appointment.client.email:
            Message.objects.create(
                client=appointment.client,
                message_type='email',
                subject=f'Appointment Cancelled: {appointment.service.name}',
                body=f'Dear {appointment.client.first_name},\n\nYour appointment for {appointment.service.name} on {appointment.date} at {appointment.time} has been cancelled.\n\nIf you did not request this cancellation, please contact us.',
                direction='outgoing',
                appointment=appointment,
                status='draft'
            )
        
        return redirect('scheduler:appointment_detail', pk=appointment.id)
    
    return render(request, 'scheduler/appointment_cancel.html', {'appointment': appointment})


# Message Views
@login_required
def message_list(request):
    """List all messages"""
    messages = Message.objects.all().order_by('-created_at')
    
    # Filtering
    message_type = request.GET.get('type')
    if message_type:
        messages = messages.filter(message_type=message_type)
    
    status = request.GET.get('status')
    if status:
        messages = messages.filter(status=status)
    
    # Pagination
    paginator = Paginator(messages, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'message_type': message_type,
        'status': status,
    }
    return render(request, 'scheduler/message_list.html', context)


@login_required
def message_create(request):
    """Create a new message"""
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.direction = 'outgoing'
            message.status = 'draft'
            message.save()
            return redirect('scheduler:message_detail', pk=message.id)
    else:
        form = MessageForm()
    
    return render(request, 'scheduler/message_form.html', {'form': form, 'mode': 'create'})


@login_required
def message_detail(request, pk):
    """View message details"""
    message = get_object_or_404(Message, pk=pk)
    return render(request, 'scheduler/message_detail.html', {'message': message})


@login_required
def message_send(request, pk):
    """Send a draft message"""
    message = get_object_or_404(Message, pk=pk)
    
    if message.send():
        return redirect('scheduler:message_detail', pk=message.id)
    else:
        return render(request, 'scheduler/message_detail.html', {
            'message': message,
            'error': 'Failed to send message'
        })


# Reminder Views
@login_required
def reminder_list(request):
    """List all reminders"""
    reminders = Reminder.objects.all().order_by('-appointment__date', '-appointment__time')
    
    # Filtering
    reminder_type = request.GET.get('type')
    if reminder_type:
        reminders = reminders.filter(reminder_type=reminder_type)
    
    sent_status = request.GET.get('sent')
    if sent_status:
        reminders = reminders.filter(sent=sent_status == 'true')
    
    context = {
        'reminders': reminders,
        'reminder_type': reminder_type,
        'sent_status': sent_status,
    }
    return render(request, 'scheduler/reminder_list.html', context)


@login_required
def reminder_create(request):
    """Create a new reminder"""
    if request.method == 'POST':
        form = ReminderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('scheduler:reminder_list')
    else:
        form = ReminderForm()
    
    return render(request, 'scheduler/reminder_form.html', {'form': form})


# iCalendar / CalDAV Views
@login_required
def ical_feed(request):
    """Export all appointments as iCalendar feed"""
    config = ScheduleConfiguration.get_config()
    
    if not config.enable_caldav:
        return HttpResponse('CalDAV is not enabled', status=403)
    
    appointments = Appointment.objects.filter(
        status__in=['scheduled', 'confirmed']
    ).order_by('date', 'time')
    
    # Combine all appointments into one calendar
    import icalendar
    cal = icalendar.Calendar()
    cal.add('prodid', f'-//{config.business_name}//Scheduler//')
    cal.add('version', '2.0')
    
    for appointment in appointments:
        event_data = appointment.to_ical()
        event = icalendar.Event.from_ical(event_data.decode('utf-8'))
        for component in event.walk():
            cal.add_component(component)
    
    response = HttpResponse(cal.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = 'attachment; filename=calendar.ics'
    return response


@login_required
def appointment_ical(request, appointment_id):
    """Export single appointment as iCalendar"""
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    response = HttpResponse(appointment.to_ical(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename=appointment_{appointment.id}.ics'
    return response
