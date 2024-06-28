from django.shortcuts import render, redirect, get_object_or_404
from .models import Service, Order, OrderItem, Payment
from users.models import Client
from visits.models import Visit
from django.contrib.auth.decorators import login_required
from django.utils import timezone
# from django.db.models import Count
from users.forms import ServiceForm, OrderItemForm, PaymentForm


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

                # Add a point to the client only upon payment & Create a new visit record
                client = order.client
                Visit.objects.create(client=client)
                
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