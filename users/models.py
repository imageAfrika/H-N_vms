from django.db import models

class Client(models.Model):
    first_name = models.CharField(max_length=100)
    second_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    points = models.IntegerField(default=0)
    referral_points = models.IntegerField(default=0)
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