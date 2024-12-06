from django.urls import path, include
from testi_vouchers.views import voucher, purchase_voucher

app_name = 'testi_vouchers'

urlpatterns = [
    path('vouchers/', voucher, name='vouchers'),
    path('vouchers/purchase/', purchase_voucher, name='purchase_voucher'),

]