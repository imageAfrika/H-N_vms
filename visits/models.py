from django.db import models
from users.models import Client

class Visit(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Increment client points on visit creation
        super().save(*args, **kwargs)
        self.client.points += 1
        self.client.save()

    def __str__(self):
        return f"{self.client.first_name}"