from django.urls import path, include
from main.views import show_main, service, subcategory

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('', include('mypay_service.urls')),
    path('service/', service, name='service'),
    path('subcategory/', subcategory, name='subcategory'),
]