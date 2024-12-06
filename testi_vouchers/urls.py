from django.urls import path, include
from testi_vouchers.views import vouchers 

app_name = 'testi_vouchers'

urlpatterns = [
    path('vouchers/', vouchers, name='vouchers'),
    
]