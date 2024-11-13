
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('', include('mypay_service.urls')),
    path('', include('testi_vouchers.urls')),
    path('auth/', include('authentication.urls', namespace='authentication')),

]
