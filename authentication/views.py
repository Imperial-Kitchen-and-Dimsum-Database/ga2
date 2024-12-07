
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

        if not phone_number or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'login.html')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(rf"""
                SET search_path TO public;
                SELECT id FROM "USER" WHERE phonenum = %s AND pwd = %s;
                """, [phone_number, password])
                user = cursor.fetchone()

            if user:
                user_id = user[0] 
                print(f"user id: {user_id}")
                user_name = None
                with connection.cursor() as cursor:
                    cursor.execute(rf"""
                    SET search_path TO public;
                    SELECT name
                    FROM "USER"
                    WHERE phonenum = %s;
                    """, [phone_number])
                    user_name_data = cursor.fetchone()
                    if user_name_data:
                        user_name = user_name_data[0]
                # Determine the user's role
                user_role = None
                with connection.cursor() as cursor:
                    cursor.execute(rf"""
                    SELECT id FROM "WORKER" WHERE id = %s;
                    """, [user_id])
                    worker = cursor.fetchone()

                    if worker:
                        user_role = 'worker'
                    else:
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
                    response.set_cookie('username', user_name)  # Set user name as a cookie
                    response.set_cookie('user_role', user_role)  # Set user role cookie
                    response.set_cookie('last_login', str(datetime.datetime.now()))
                    response.set_cookie('user_id', user_id)
                    return response
                else:
                    messages.error(request, "Unable to determine user role")
                    
            else:
                messages.error(request, "Sorry, incorrect username or password. Please try again.")

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

        return render(request, 'login.html')

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
    response.delete_cookie('user_id')
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
        
        if not all([name, phone_number, sex, password, dob, address]):
            messages.error(request, "All fields are required.")
            return render(request, 'register_appuser.html')

        try:
            user_id = str(uuid.uuid4())  
            
            with connection.cursor() as cursor:
                cursor.execute(rf"""
                SET search_path TO public;
                INSERT INTO "USER" (id, name, sex, phonenum, pwd, dob, address, mypaybalance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """, [user_id, name, sex, phone_number, password, dob, address, 0])

                cursor.execute(rf"""
                INSERT INTO "CUSTOMER" (id, level)
                VALUES (%s, %s);
                """, [user_id, 0])
            
            messages.success(request, "Registration successful!")
            return redirect('authentication:login')
        
        except Exception as e:
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
        pic_url = request.POST.get('image_url') 
        rate = request.POST.get('rate', 0) 
        total_finish_order = request.POST.get('totalfinishorder', 0)

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

from django.db import connection
from django.contrib import messages
from django.shortcuts import render, redirect

def profile(request):
    user_role = request.COOKIES.get('user_role')
    phone_number = request.COOKIES.get('phone_number')
    
    if not phone_number or not user_role:
        messages.error(request, "You must log in to access your profile.")
        return redirect('authentication:login')
    
    if request.method == "POST":
        name = request.POST.get('name')
        password = request.POST.get('password')
        sex = request.POST.get('sex')
        birth_date = request.POST.get('birth_date')
        address = request.POST.get('address')

        if not all([name, password, sex, birth_date, address]):
            messages.error(request, "All fields are required.")
            print("all fields required")
            return redirect('authentication:profile')

        if user_role == "worker":
            bank_name = request.POST.get('bank_name')
            account_number = request.POST.get('account_number')
            npwp = request.POST.get('npwp')
            profile_picture = request.POST.get('image_url') 

            if not all([bank_name, account_number, npwp]):
                messages.error(request, "All fields, including bank details, NPWP, rate, and total orders, are required for workers.")
                return redirect('authentication:profile')

            try:
                with connection.cursor() as cursor:
                    cursor.execute(rf"""
                    SET search_path TO public;
                    SELECT id FROM "USER" WHERE phonenum = %s;
                    """, [phone_number])
                    
                    user_id = cursor.fetchone()
                    
                    if user_id:
                        user_id = user_id[0]  

                        cursor.execute(rf"""
                        SET search_path TO public;
                        UPDATE "USER"
                        SET name = %s, pwd = %s, sex = %s, dob = %s, address = %s
                        WHERE phonenum = %s;
                        """, [name, password, sex, birth_date, address, phone_number])

                        cursor.execute(rf"""
                        SET search_path TO public;
                        UPDATE "WORKER"
                        SET bankname = %s, accnumber = %s, npwp = %s, picurl = %s
                        WHERE id = %s;
                        """, [bank_name, account_number, npwp, profile_picture, user_id])

                        messages.success(request, "Profile updated successfully!")
                    else:
                        messages.error(request, "User not found.")
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('authentication:profile')


    try:
        with connection.cursor() as cursor:
            cursor.execute(rf"""
            SET search_path TO public;
            SELECT id, name, sex, phonenum, pwd, dob, address, mypaybalance
            FROM "USER"
            WHERE phonenum = %s;
            """, [phone_number])
            user = cursor.fetchone()

        if not user:
            messages.error(request, "User not found.")
            return redirect('authentication:login')

        user_data = {
            "id": user[0],
            "name": user[1],
            "sex": user[2],
            "phone": user[3],
            "password": user[4],
            "birth_date": user[5],
            "address": user[6],
            "pay_balance": user[7],
        }

        if user_role == "worker":
            with connection.cursor() as cursor:
                cursor.execute(rf"""
                SET search_path TO public;
                SELECT bankname, accnumber, npwp, picurl, rate, totalfinishorder
                FROM "WORKER"
                WHERE id = %s;
                """, [user_data["id"]])
                worker_data = cursor.fetchone()

            if worker_data:
                user_data.update({
                    "bank_name": worker_data[0],
                    "account_number": worker_data[1],
                    "npwp": worker_data[2],
                    "profile_picture": worker_data[3],
                    "rate": worker_data[4],
                    "total_finished_orders": worker_data[5],
                })

            return render(request, "profile_worker.html", {"user": user_data})

        elif user_role == "appuser":
            with connection.cursor() as cursor:
                cursor.execute(rf"""
                SET search_path TO public;
                SELECT level
                FROM "CUSTOMER"
                WHERE id = %s;
                """, [user_data["id"]])
                customer_data = cursor.fetchone()

            if customer_data:
                user_data.update({
                    "level": customer_data[0],
                })

            return render(request, "profile_appuser.html", {"user": user_data})

        else:
            messages.error(request, "Invalid user role.")
            return redirect('authentication:login')

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('authentication:login')
