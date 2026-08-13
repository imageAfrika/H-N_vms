from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, Referral, Notification
from scheduler.models import Appointment
from visits.models import Visit
from services.models import Service, Order, OrderItem, Payment
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import date
from django.http import JsonResponse


def index(request):
    """Home page dashboard"""
    today = timezone.now().date()
    
    # Get today's stats
    clients_today = Client.objects.filter(date_joined__date=today) if hasattr(Client, 'date_joined') else Client.objects.none()
    visits_today = Visit.objects.filter(visit_time__date=today)
    
    # Get recent notifications
    notifications = Notification.objects.filter(is_read=False).order_by('-created_at')[:10]
    
    # Get upcoming birthdays (next 7 days)
    upcoming_birthdays = []
    for client in Client.objects.exclude(date_of_birth=None):
        if client.date_of_birth:
            this_year_birthday = date(today.year, client.date_of_birth.month, client.date_of_birth.day)
            if this_year_birthday >= today and (this_year_birthday - today).days <= 7:
                upcoming_birthdays.append({
                    'client': client,
                    'days_until': (this_year_birthday - today).days,
                    'birthday': this_year_birthday
                })
    
    # Sort by days until birthday
    upcoming_birthdays.sort(key=lambda x: x['days_until'])
    
    # Get recent clients
    recent_clients = Client.objects.all().order_by('-id')[:5] if hasattr(Client, 'date_joined') else Client.objects.all()[:5]
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        date__gte=today,
        status='scheduled'
    ).order_by('date', 'time')[:5]
    
    context = {
        'clients_today': clients_today,
        'visits_today': visits_today,
        'notifications': notifications,
        'upcoming_birthdays': upcoming_birthdays,
        'recent_clients': recent_clients,
        'total_clients': Client.objects.count(),
        'total_services': Service.objects.count(),
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
        'clients': Client.objects.all(),
        'services': Service.objects.all(),
        'upcoming_appointments': upcoming_appointments,
    }
    return render(request, 'users/index.html', context)

@login_required
def visit(request, client_id):
    """Log visit"""
    client = Client.objects.get(id=client_id)
    Visit(client=client).save()
    return redirect('users:client_detail', client_id=client.id)

def daily_visits(request):
    """Daily visits"""
    today = timezone.now().date()
    
    # Filter visits for today
    visits_today = Visit.objects.filter(visit_time__date=today).select_related('client')
    context = {'visits_today': visits_today, 'today': today}
    return render(request, 'users/daily_visits.html', context)

@login_required
def redeem_points(request, client_id):
    """Redeem visit points"""
    client = Client.objects.get(id=client_id)
    client.redeem_points()
    return redirect('users:client_detail', client_id=client.id)

@login_required
def redeem_referral_points(request, client_id):
    """Redeem referral points"""
    client = Client.objects.get(id=client_id)
    client.redeem_referral_points()
    return redirect('users:client_detail', client_id=client.id)

def redeem_birthday_points(request, client_id):
    """Redeem birthday points"""
    client = Client.objects.get(id=client_id)
    client.redeem_birthday_points()
    return redirect('users:client_detail', client_id=client.id)

@login_required
def client_list(request):
    """Show all clients"""
    clients = Client.objects.all()
    context = {'clients': clients}
    return render(request, 'users/client_list.html', context)

@login_required
def client_detail(request, client_id):
    """Show each client details"""
    client = Client.objects.get(id=client_id)
    visits = client.visit_set.order_by('-visit_time')[:5]
    context = {'client': client, 'visits': visits}
    return render(request, 'users/client_detail.html', context)

@login_required
def register_client(request):
    """Register a new client"""
    if request.method == 'POST':
        first_name = request.POST['first_name']
        second_name = request.POST['second_name']
        email = request.POST['email']
        phone = request.POST['phone']
        date_of_birth = request.POST.get('date_of_birth', None)
        referred_by_id = request.POST.get('referred_by', None)
        card_paid = request.POST.get('card_paid', 'off') == 'on'
        card_issued = request.POST.get('card_issued', 'off') == 'on'

        referred_by = Client.objects.get(id=referred_by_id) if referred_by_id else None
        
        client = Client(
            first_name=first_name,
            second_name=second_name,
            email=email,
            phone=phone,
            date_of_birth=date_of_birth,
            referred_by=referred_by,
            card_paid=card_paid,
            card_issued=card_issued
        )
        client.save()
        
        if referred_by:
            referral = Referral(referrer=referred_by, referred_client=client)
            referral.save()
        
        return redirect('users:client_list')
    
    clients = Client.objects.all()
    context = {'clients': clients}
    return render(request, 'registration/register_client.html', context)

# search
@login_required
def search(request):
    """Search for client"""
    query = request.GET.get('query', '')
    clients = Client.objects.filter(Q(first_name__icontains=query))
    search_count = clients.count()

    context = {'clients': clients, 'query': query, 'search_count': search_count}
    return render(request, 'users/search.html', context)


#Log out
from django.contrib.auth import logout

@login_required
def logout_view(request):
    logout(request)
    return render(request, 'registration/logged_out.html')  # Redirect to login page after logout


@login_required
def create_appointment(request):
    """Create a new appointment via AJAX"""
    if request.method == 'POST':
        try:
            client_id = request.POST.get('client')
            service_id = request.POST.get('service')
            appointment_date = request.POST.get('date')
            appointment_time = request.POST.get('time')
            notes = request.POST.get('notes', '')
            
            client = get_object_or_404(Client, id=client_id)
            service = get_object_or_404(Service, id=service_id)
            
            from datetime import datetime, timedelta
            appointment = Appointment.objects.create(
                client=client,
                service=service,
                date=appointment_date,
                time=appointment_time,
                notes=notes,
                status='scheduled'
            )
            
            # Create default reminder
            from scheduler.models import Reminder, ScheduleConfiguration
            config = ScheduleConfiguration.get_config()
            default_reminder_hours = config.reminder_default_hours
            Reminder.objects.create(
                appointment=appointment,
                reminder_type='email',
                remind_before=timedelta(hours=default_reminder_hours)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Appointment scheduled successfully',
                'appointment_id': appointment.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)


@login_required
def appointment_list(request):
    """Display all appointments"""
    appointments = Appointment.objects.all().order_by('date', 'time')
    context = {'appointments': appointments}
    return render(request, 'users/appointment_list.html', context)
