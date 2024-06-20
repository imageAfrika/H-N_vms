from django.shortcuts import render, redirect
from .models import Client, Referral
from visits.models import Visit

def visit(request, client_id):
    """Log visit"""
    client = Client.objects.get(id=client_id)
    Visit(client=client).save()
    return redirect('users:client_detail', client_id=client.id)

def redeem_points(request, client_id):
    """Redeem visit points"""
    client = Client.objects.get(id=client_id)
    client.redeem_points()
    return redirect('users:client_detail', client_id=client.id)

def redeem_referral_points(request, client_id):
    """Redeem referral points"""
    client = Client.objects.get(id=client_id)
    client.redeem_referral_points()
    return redirect('users:client_detail', client_id=client.id)

def client_list(request):
    """Show all clients"""
    clients = Client.objects.all()
    context = {'clients': clients}
    return render(request, 'users/client_list.html', context)

def client_detail(request, client_id):
    """Show each client details"""
    client = Client.objects.get(id=client_id)
    context = {'client': client}
    return render(request, 'users/client_detail.html', context)

def register_client(request):
    """Register a new user"""
    if request.method == 'POST':
        first_name = request.POST['first_name']
        second_name = request.POST['second_name']
        email = request.POST['email']
        phone = request.POST['phone']
        referred_by_id = request.POST.get('referred_by', None)
        card_paid = request.POST.get('card_paid', 'off') == 'on'
        card_issued = request.POST.get('card_issued', 'off') == 'on'

        referred_by = Client.objects.get(id=referred_by_id) if referred_by_id else None
        
        client = Client(
            first_name=first_name,
            second_name=second_name,
            email=email,
            phone=phone,
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
    return render(request, 'users/register_client.html', {'clients': clients})