from django.db import models
from django.utils import timezone
from users.models import Client

class Service(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calculate_total(self):
        self.total = sum(item.service.price for item in self.orderitem_set.all())
        self.save()

    def __str__(self):
        return f"Order {self.id} for {self.client.first_name} {self.client.second_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.service.name} (x{self.quantity})"

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('paybill', 'Paybill'),
        ('till_number', 'Till Number')
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.method}: {self.amount}"
