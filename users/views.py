from django.shortcuts import render, redirect
from .models import Client, Referral
from visits.models import Visit
from django.contrib.auth.decorators import login_required
from django.db.models import Q

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
    context = {'client': client}
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

@login_required
def search(request):
    """Search for items"""
    query = request.GET.get('query', '')
    clients = Client.objects.filter(Q(name__icontains=query))
    search_count = clients.count()

    context = {'clients': clients, 'query': query, 'search_count': search_count}
    return render(request, 'products/search.html', context)