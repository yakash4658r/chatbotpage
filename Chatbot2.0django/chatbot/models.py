from django.db import models

class Order(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    plan = models.CharField(max_length=100, default="Starter")
    amount = models.FloatField()
    orderId = models.CharField(max_length=100, unique=True)
    paymentStatus = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.orderId}"