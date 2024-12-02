
import datetime
from django.http import HttpResponseRedirect  
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.db.utils import IntegrityError

import uuid
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages

def hero(request):
    return render(request, "hero.html")

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        messages = []

        if not phone_number or not password:
            messages.append('Username and password are required.')
        
        if messages:
            return render(request, 'login.html', {'messages': messages})

        try:
            with connection.cursor() as cursor:
                # Check if the user exists in the USER table
                cursor.execute(rf"""
                SET search_path TO public;
                SELECT id FROM "USER" WHERE phonenum = %s AND pwd = %s;
                """, [phone_number, password])
                user = cursor.fetchone()

            if user:
                user_id = user[0]  # Fetch the user's UUID

                # Determine the user's role
                user_role = None
                with connection.cursor() as cursor:
                    # Check if the user is a worker
                    cursor.execute(rf"""
                    SELECT id FROM "WORKER" WHERE id = %s;
                    """, [user_id])
                    worker = cursor.fetchone()

                    if worker:
                        user_role = 'worker'
                    else:
                        # Check if the user is a customer
                        cursor.execute(rf"""
                        SELECT id FROM "CUSTOMER" WHERE id = %s;
                        """, [user_id])
                        customer = cursor.fetchone()
                        if customer:
                            user_role = 'appuser'

                # Set session and cookies
                if user_role:
                    request.session['phone_number'] = phone_number
                    response = HttpResponseRedirect(reverse("main:show_main"))
                    response.set_cookie('phone_number', phone_number)
                    response.set_cookie('user_role', user_role)  # Set user role cookie
                    response.set_cookie('last_login', str(datetime.datetime.now()))
                    return response
                else:
                    messages.append('Unable to determine user role.')
            else:
                messages.append('Sorry, incorrect username or password. Please try again.')

        except Exception as e:
            messages.append(f"An error occurred: {str(e)}")

        return render(request, 'login.html', {'messages': messages})

    return render(request, 'login.html')

@csrf_exempt
def logout_user(request):
    with connection.cursor() as cursor:
                cursor.execute(rf"""
                SET search_path to public; 
                """)
    response = HttpResponseRedirect(reverse('main:show_main'))
    request.session.flush()
    response.delete_cookie('last_login')
    response.delete_cookie('phone_number')
    return response

def choose_role(request):
    if request.method == "POST":
        role = request.POST.get('role')

        if role == 'worker':
            return redirect('authentication:register_worker')
        elif role == 'appuser':
            return redirect('authentication:register_appuser')

    return render(request, 'choose_role.html')

def register_appuser(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone')
        sex = request.POST.get('sex') 
        password = request.POST.get('password')
        dob = request.POST.get('birthdate') 
        address = request.POST.get('address')
        
        # Ensure all fields are filled
        if not all([name, phone_number, sex, password, dob, address]):
            messages.error(request, "All fields are required.")
            return render(request, 'register_appuser.html')

        try:
            user_id = str(uuid.uuid4())  # Generate UUID for the user
            
            # Use a single transaction
            with connection.cursor() as cursor:
                cursor.execute(rf"""
                SET search_path TO public;
                INSERT INTO "USER" (id, name, sex, phonenum, pwd, dob, address, mypaybalance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, [user_id, name, sex, phone_number, password, dob, address, 0])

                # Insert into CUSTOMER table
                cursor.execute(rf"""
                INSERT INTO "CUSTOMER" (id, level)
                VALUES (%s, %s);
                """, [user_id, 0])
            
            messages.success(request, "Registration successful!")
            return redirect('authentication:login')
        
        except Exception as e:
            # Rollback the transaction if an error occurs
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'register_appuser.html')
    
    return render(request, 'register_appuser.html')

def register_worker(request):
    if request.method == 'POST':
        # Collect data from the form
        name = request.POST.get('name')
        phone_number = request.POST.get('phone')
        sex = request.POST.get('sex')
        password = request.POST.get('password')
        dob = request.POST.get('birthdate')
        address = request.POST.get('address')
        bank_name = request.POST.get('bank_name')
        acc_number = request.POST.get('account_number')
        npwp = request.POST.get('npwp')
        pic_url = request.POST.get('image_url')  # Profile picture URL
        rate = request.POST.get('rate', 0)  # Default rate to 0 if not provided
        total_finish_order = request.POST.get('totalfinishorder', 0)  # Default to 0

        if not all([name, phone_number, sex, password, dob, address, bank_name, acc_number, npwp, pic_url]):
            messages.error(request, "All fields are required.")
            return render(request, 'register_worker.html')

        try:
            user_id = str(uuid.uuid4())

            with connection.cursor() as cursor:
                cursor.execute(rf"""
                SET search_path TO public;
                INSERT INTO "USER" (id, name, sex, phonenum, pwd, dob, address, mypaybalance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, [user_id, name, sex, phone_number, password, dob, address, 0])

                cursor.execute(rf"""
                INSERT INTO "WORKER" (id, bankname, accnumber, npwp, picurl, rate, totalfinishorder)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, [user_id, bank_name, acc_number, npwp, pic_url, rate, total_finish_order])

            messages.success(request, "Worker registration successful!")
            return redirect('authentication:login')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'register_worker.html')

    return render(request, 'register_worker.html')

def profile(request):
    # Retrieve the user role from cookies
    user_role = request.COOKIES.get('user_role')

    # Check the user role and render the appropriate template
    if user_role == "worker":
        return render(request, "profile_worker.html")
    elif user_role == "appuser":  # 'user' corresponds to an app user
        return render(request, "profile_appuser.html")
    else:
        # Redirect to login page if the role is not defined
        messages.error(request, "You must log in to access your profile.")
        return redirect('authentication:login')

