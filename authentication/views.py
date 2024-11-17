from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm 
from .models import CustomUser
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate


def hero(request):
    return render(request, "hero.html")

def login_user(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')

        user = authenticate(request, phone=phone_number, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in.')
            return redirect('main:show_main')  
        else:
            messages.error(request, 'Invalid credentials, please try again.')
            return redirect('authentication:login') 

    return render(request, 'login.html')

def logout_user(request):
    logout(request)
    response = HttpResponseRedirect(reverse('authentication:login'))
    response.delete_cookie('last_login')
    return redirect('authentication:hero')

def choose_role(request):
    if request.method == "POST":
        role = request.POST.get('role')

        if role == 'worker':
            return redirect('authentication:register_worker')
        elif role == 'appuser':
            return redirect('authentication:register_appuser')

    return render(request, 'choose_role.html')

def register_worker(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        if phone and password: 
            user = CustomUser(
                phone=phone,
                password=password,
                user_type='worker'  
            )
            user.set_password(password)  
            user.save()  
            messages.success(request, 'Worker account created successfully.')
            return redirect('authentication:login')  
        else:
            messages.error(request, 'All fields required.')

    return render(request, 'register_worker.html')

def register_appuser(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        if phone and password:
            user = CustomUser(
                phone=phone,
                password=password,  
                user_type='appuser' 
            )
            user.set_password(password) 
            user.save()  
            messages.success(request, 'App user account created successfully.')
            return redirect('authentication:login')  
        else:
            messages.error(request, 'All fields must be filled')

    return render(request, 'register_appuser.html')

def profile(request):
    role = request.user.user_type
    if role == "worker":
        return render(request, "profile_worker.html")
    elif role == "appuser":
        return render(request, "profile_appuser.html")
