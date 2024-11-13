    
from django.urls import path, include
from authentication.views import temp_hero

app_name = 'authentication'

urlpatterns = [
    path('temp_hero/', temp_hero, name='temp_hero'),
]