from django.urls import path
from .views import mypay_dashboard, transfer_money, topup_balance, all_transactions, withdraw_balance

app_name = 'mypay_service'

urlpatterns = [
    path('mypay/', mypay_dashboard, name='mypay_dashboard'),
    path('mypay/topup/', topup_balance, name='topup_balance'),
    path('mypay/transfer/', transfer_money, name='transfer_money'),
    path('transactions/', all_transactions, name='all_transactions'),
    path('mypay/withdraw/', withdraw_balance, name='withdraw_balance')
]