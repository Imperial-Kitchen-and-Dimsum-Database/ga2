    
from django.urls import path
from authentication.views import hero,login_user, logout_user, register_worker, register_appuser, choose_role

app_name = 'authentication'

urlpatterns = [
    path('hero/', hero, name='hero'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('register_worker/', register_worker, name='register_worker'),
    path('choose-role/', choose_role, name='choose_role'),  # URL for choosing role
    path('register_appuser/', register_appuser, name='register_appuser'),
]