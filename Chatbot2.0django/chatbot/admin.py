from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'plan', 'amount', 'paymentStatus', 'created_at')
    list_filter = ('paymentStatus', 'plan')