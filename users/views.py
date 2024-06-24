from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, Referral
from visits.models import Visit
from services.models import Service, Order, OrderItem, Payment
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.db.models import Count
from .forms import ClientForm, ServiceForm, OrderItemForm, PaymentForm

def index(request):
    """Home page"""
    context = {}
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
    return render(request, 'users/register_client.html', context)

# search
@login_required
def search(request):
    """Search for client"""
    query = request.GET.get('query', '')
    clients = Client.objects.filter(Q(first_name__icontains=query))
    search_count = clients.count()

    context = {'clients': clients, 'query': query, 'search_count': search_count}
    return render(request, 'users/search.html', context)

# service
@login_required
def service_list(request):
    """Show all services"""
    services = Service.objects.all()
    context = {'services': services}
    return render(request, 'services/service_list.html', context)

@login_required
def add_service(request):
    """Add a new service"""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('services:service_list')
    else:
        form = ServiceForm()
    context = {'form': form}
    return render(request, 'services/add_service.html', context)

@login_required
def edit_service(request, service_id):
    """Edit a service"""
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect('services:service_list')
    else:
        form = ServiceForm(instance=service)
    context = {'form': form}
    return render(request, 'services/edit_service.html', context)

@login_required
def delete_service(request, service_id):
    """Delete a service"""
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        service.delete()
        return redirect('services:service_list')
    context = {'service': service}
    return render(request, 'services/delete_service.html', context)

@login_required
def create_order(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    order, created = Order.objects.get_or_create(client=client, status='pending')
    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        if form.is_valid():
            order_item = form.save(commit=False)
            order_item.order = order
            order_item.save()
            order.calculate_total()
            return redirect('services:edit_order', order.id)
    else:
        form = OrderItemForm()
    return render(request, 'services/create_order.html', {'form': form, 'order': order})

@login_required
def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        if form.is_valid():
            order_item = form.save(commit=False)
            order_item.order = order
            order_item.save()
            order.calculate_total()
            return redirect('services:edit_order', order.id)
    else:
        form = OrderItemForm()
    return render(request, 'services/edit_order.html', {'form': form, 'order': order})

@login_required
def delete_order_item(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id)
    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
    if request.method == 'POST':
        order_item.delete()
        order.calculate_total()
        return redirect('services:edit_order', order.id)
    return render(request, 'services/delete_order_item.html', {'order': order, 'order_item': order_item})

@login_required
def proceed_to_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.save()
            if sum(payment.amount for payment in order.payment_set.all()) >= order.total:
                order.status = 'completed'
                order.save()
            return redirect('services:order_detail', order.id)
    else:
        form = PaymentForm()
    return render(request, 'services/proceed_to_payment.html', {'form': form, 'order': order})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'services/order_detail.html', {'order': order})

@login_required
def daily_payments_summary(request):
    payments = Payment.objects.filter(order__created_at__date=timezone.now().date())
    summary = payments.values('method').annotate(total_amount=models.Sum('amount'))
    return render(request, 'services/daily_payments_summary.html', {'summary': summary})