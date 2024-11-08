from django.urls import path
from .views import mypay_dashboard

urlpatterns = [
    path('mypay/', mypay_dashboard, name='mypay_dashboard'),
]