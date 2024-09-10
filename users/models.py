from django.db import models
from datetime import date
from django.utils import timezone

class Client(models.Model):
    first_name = models.CharField(max_length=100)
    second_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    points = models.IntegerField(default=0)
    referral_points = models.IntegerField(default=0)
    date_of_birth = models.DateField(null=True, blank=True)
    birthday_points = models.IntegerField(default=0)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    card_paid = models.BooleanField(default=False)
    card_issued = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name
    
    def redeem_points(self):
        if self.points >= 3:
            self.points -= 3
            self.save()
    
    def redeem_referral_points(self):
        if self.referral_points >= 3:
            self.referral_points -= 3
            self.save()

    def add_birthday_points(self):
        if self.date_of_birth and self.date_of_birth.month == date.today().month and self.date_of_birth.day == date.today().day:
            self.birthday_points += 5
            self.save()

    def redeem_birthday_points(self):
        if self.birthday_points >= 5:
            self.birthday_points -= 5
            self.save()


class Referral(models.Model):
    referrer = models.ForeignKey(Client, related_name='referrals', on_delete=models.CASCADE)
    referred_client = models.OneToOneField(Client, related_name='referral', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Increment referrer referral points on referral creation
        super().save(*args, **kwargs)
        self.referrer.referral_points += 1
        self.referrer.save()

    def __str__(self):
        return f"{self.referrer.first_name}"