from django import forms
from .models import Client
from services.models import Service, OrderItem, Payment

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['first_name', 'second_name', 'email', 'phone', 'date_of_birth', 'referred_by', 'card_paid', 'card_issued']

# service
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'price']

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['service', 'quantity']

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['method', 'amount']