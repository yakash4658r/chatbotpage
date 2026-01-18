from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create-order/', views.create_order, name='create_order'),
    path('payment-status/', views.payment_status, name='payment_status'),
]