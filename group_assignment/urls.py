
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    # path('authentication/', include('authentication.urls')),
    # path('mypay_service/', include('mypay_service.urls')),
    # path('testi_vouchers/', include('testi_vouchers.urls')),
]
