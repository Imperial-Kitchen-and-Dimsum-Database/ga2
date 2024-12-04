from django.urls import path, include
from main.views import show_main, service, subcategory_page, status, worker_status, user_service_bookings, worker_profile

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('service/', service, name='service'),
    path('subcategory/<uuid:subcategory_id>/', subcategory_page, name='subcategory'),
    path('status/', status, name='status'),
    path('worker_status/', worker_status, name='worker_status'),
    path('user_service_bookings/', user_service_bookings, name='user_service_bookings'),
    path('worker/<uuid:worker_id>/', worker_profile, name='worker_profile'),
]