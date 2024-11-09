from django.urls import path
from .views import mypay_dashboard

app_name = 'mypay_service'

urlpatterns = [
    path('mypay/', mypay_dashboard, name='mypay_dashboard'),
]