from django.urls import path, include
from main.views import show_main, service, subcategory_page, status, worker_status

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('service/', service, name='service'),
    path('subcategory/', subcategory_page, name='subcategory'),
    path('status/', status, name='status'),
    path('worker_status/', worker_status, name='worker_status'),
]