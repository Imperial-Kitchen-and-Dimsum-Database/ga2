from django.shortcuts import render
from functools import wraps
from django.shortcuts import redirect
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from uuid import uuid4
import datetime
import random

def login_required(view_func=None, login_url='authentication:login'):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # check if phone_number is in the session
            if 'phone_number' not in request.session:
                return redirect(login_url)
            return func(request, *args, **kwargs)
        return wrapper

    # if used as @login_required with no parentheses
    if view_func:
        return decorator(view_func)
    return decorator


@login_required(login_url='/auth/hero/')
def show_main(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT sc.CategoryName as category_name,
                   json_agg(json_build_object('id', ss.Id, 'name', ss.SubcategoryName)) as subcategories
            FROM "SERVICE_CATEGORY" sc
            LEFT JOIN "SERVICE_SUBCATEGORY" ss ON sc.Id = ss.ServiceCategoryId
            GROUP BY sc.Id, sc.CategoryName
        """)

        categories = {}
        for row in cursor.fetchall():
            categories[row[0]] = row[1]

    context = {
        'categories': categories,
    }
    return render(request, "main.html", context)

def service(request):
    return render(request, "service_details.html")

def subcategory_page(request, subcategory_id):
    user_id = request.COOKIES.get('user_id')
    user_role = request.COOKIES.get('user_role')
    has_joined = False

    if request.method == "POST":
        if "join_worker" in request.POST:  
            try:
                service_category_id = request.POST.get("service_category_id")
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO "WORKER_SERVICE_CATEGORY" (WorkerId, ServiceCategoryId)
                        VALUES (%s, %s)
                    """, [user_id, service_category_id])
                return redirect("main:subcategory", subcategory_id=subcategory_id)
            
            except Exception as e:
                print(f"Error: {e}")
                return render(request, "subcategory_page.html", {
                    'subcategory_name': subcategory[0],
                    'description': subcategory[1],
                    'category_name': subcategory[2],
                    'service_category_id': subcategory[3],
                    'sessions': sessions,
                    'workers': workers,
                    'has_joined': has_joined,
                    'payment_methods': payment_methods,
                    'user_role': user_role,
                    'error': 'Failed to join as a worker. Please try again.'
                })

        elif "book_service" in request.POST: 
            try:
                session_name = request.POST.get("service_name")
                total_payment = request.POST.get("total_payment")
                discount_code = request.POST.get("discount_code") or None
                payment_method_id = request.POST.get("payment_method")
                order_date = request.POST.get("order_date")  

                session_number = int(session_name.split(" ")[1])  

                parsed_order_date = datetime.datetime.strptime(order_date, "%d/%m/%Y")

                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO "TR_SERVICE_ORDER" (
                            Id, orderDate, serviceDate, serviceTime, 
                            TotalPrice, customerId, serviceCategoryId, Session, 
                            discountCode, paymentMethodId
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, [
                        str(uuid4()),  
                        parsed_order_date,
                        parsed_order_date,  
                        parsed_order_date,  
                        total_payment,
                        user_id,
                        subcategory_id,
                        session_number,
                        discount_code,
                        payment_method_id,
                    ])
                return redirect("main:user_service_bookings")

            except Exception as e:
                print(f"Error: {e}")
                return render(request, "subcategory_page.html", {
                    'subcategory_name': subcategory[0],
                    'description': subcategory[1],
                    'category_name': subcategory[2],
                    'service_category_id': subcategory[3],
                    'sessions': sessions,
                    'workers': workers,
                    'has_joined': has_joined,
                    'payment_methods': payment_methods,
                    'user_role': user_role,
                    'error': 'Failed to book the service. Please try again.'
                })

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT ss.SubcategoryName, ss.Description, sc.CategoryName, sc.Id AS ServiceCategoryId
            FROM "SERVICE_SUBCATEGORY" ss
            LEFT JOIN "SERVICE_CATEGORY" sc ON ss.ServiceCategoryId = sc.Id
            WHERE ss.Id = %s
        """, [subcategory_id])
        subcategory = cursor.fetchone()

        if not subcategory:
            return render(request, '404.html', {'error': 'Subcategory not found.'})

        cursor.execute("""
            SELECT Session, Price
            FROM "SERVICE_SESSION"
            WHERE SubcategoryId = %s
        """, [subcategory_id])
        sessions = [
            {
                'name': f'Session {row[0]}',
                'price': row[1],
            }
            for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT w.Id, u.Name, w.PicURL, w.TotalFinishOrder, w.Rate
            FROM "WORKER_SERVICE_CATEGORY" wsc
            JOIN "WORKER" w ON w.Id = wsc.WorkerId
            JOIN "USER" u ON u.Id = w.Id
            WHERE wsc.ServiceCategoryId = (
                SELECT ServiceCategoryId FROM "SERVICE_SUBCATEGORY" WHERE Id = %s
            )
        """, [subcategory_id])
        workers = [
            {
                'id': row[0],
                'name': row[1],
                'image': row[2],
                'experience': row[3],
                'rate': row[4],
            }
            for row in cursor.fetchall()
        ]

        if user_role == 'worker':
            cursor.execute("""
                SELECT ServiceCategoryId 
                FROM "SERVICE_SUBCATEGORY" 
                WHERE Id = %s
            """, [subcategory_id])
            service_category = cursor.fetchone()

            if service_category:
                service_category_id = service_category[0]
                print(f"ServiceCategoryId: {service_category_id}, id: {user_id}") 

                cursor.execute("""
                    SELECT 1
                    FROM "WORKER_SERVICE_CATEGORY"
                    WHERE WorkerId = %s AND ServiceCategoryId = %s
                """, [user_id, service_category_id])
                has_joined = bool(cursor.fetchone())

        print(f"Has joined: {has_joined}")

        cursor.execute("""
            SELECT Id, Name
            FROM "PAYMENT_METHOD"
        """)
        payment_methods = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    context = {
        'subcategory_id': subcategory_id,
        'subcategory_name': subcategory[0],
        'description': subcategory[1],
        'category_name': subcategory[2],
        'service_category_id': subcategory[3],
        'sessions': sessions,
        'workers': workers,
        'has_joined': has_joined,
        'payment_methods': payment_methods,
        'user_role': user_role,
    }

    return render(request, 'subcategory_page.html', context)




def status(request):
    return render(request,"status.html" )

def worker_status(request):
    context = {
        'categories': [
            {'id': 1, 'name': 'Home Cleaning'},
            {'id': 2, 'name': 'Deep Cleaning'},
            {'id': 3, 'name': 'Air Conditioning'},
        ],
        'subcategories': [
            {'id': 1, 'category_id': 1, 'name': 'Daily Cleaning'},
            {'id': 2, 'category_id': 1, 'name': 'Ironing'},
            {'id': 3, 'category_id': 2, 'name': 'Floor Cleaning'},
        ],
        'orders': [
            {
                'id': '001',
                'category': 'Home Cleaning',
                'subcategory': 'Daily Cleaning',
                'customer': 'John Smith',
                'address': '123 Main St',
                'scheduled_time': '2024-01-20 14:00',
                'status': 'Pending'
            },
            {
                'id': '002', 
                'category': 'Deep Cleaning',
                'subcategory': 'Floor Cleaning',
                'customer': 'Jane Doe',
                'address': '456 Oak Ave',
                'scheduled_time': '2024-01-21 10:00',
                'status': 'Accepted'
            }
        ],
        'status_options': [
            'Pending',
            'Accepted',
            'Arrived at Location',
            'Providing Service', 
            'Service Completed',
            'Completed',
            'Cancelled'
        ]
    }
    return render(request, 'worker_status.html', context)

@login_required
def user_service_bookings(request):
    user_id = request.COOKIES.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tso.Id, pm.Name AS payment_method
            FROM "TR_SERVICE_ORDER" tso
            LEFT JOIN "TR_ORDER_STATUS" tos ON tso.Id = tos.serviceTrId
            LEFT JOIN "PAYMENT_METHOD" pm ON tso.paymentMethodId = pm.Id
            WHERE tso.customerId = %s AND tos.serviceTrId IS NULL
        """, [user_id])
        new_orders = cursor.fetchall()

        for order_id, payment_method in new_orders:
            initial_status_id = ("8e6a889d-c209-41bc-8b40-d4e6736960ff" if payment_method == "MyPay" else "a04e23bc-c655-4eec-8657-4733bed460f6")

            cursor.execute("""
                INSERT INTO "TR_ORDER_STATUS" (serviceTrId, statusId, date)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
            """, [order_id, initial_status_id])

        cursor.execute("""
            SELECT tso.Id, 
                   tso.orderDate, 
                   tso.TotalPrice, 
                   ssc.SubcategoryName, 
                   ss.Session, 
                   os.Status AS order_status,
                   EXISTS (
                       SELECT 1
                       FROM "TESTIMONI" t
                       WHERE t.serviceTrId = tso.Id
                   ) AS testimonial_created
            FROM "TR_SERVICE_ORDER" tso
            LEFT JOIN "SERVICE_SESSION" ss ON tso.serviceCategoryId = ss.SubcategoryId AND tso.Session = ss.Session
            LEFT JOIN "SERVICE_SUBCATEGORY" ssc ON ss.SubcategoryId = ssc.Id
            LEFT JOIN "TR_ORDER_STATUS" tos ON tos.serviceTrId = tso.Id
            LEFT JOIN "ORDER_STATUS" os ON tos.statusId = os.Id
            WHERE tso.customerId = %s
            ORDER BY tso.orderDate DESC;
        """, [user_id])

        orders = [
            {
                'order_id': row[0],
                'order_date': row[1],
                'total_payment': row[2],
                'subcategory_name': row[3],
                'session': row[4],
                'order_status': row[5],
                'testimonial_created': row[6],
            }
            for row in cursor.fetchall()
        ]

    subcategories = sorted({order['subcategory_name'] for order in orders if order['subcategory_name']})
    statuses = sorted({order['order_status'] for order in orders if order['order_status']})

    return render(request, "user_service_bookings.html", {
        'orders': orders,
        'subcategories': subcategories,
        'statuses': statuses,
    })


def worker_profile(request, worker_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.Name, 
                w.Rate, 
                w.TotalFinishOrder, 
                u.PhoneNum, 
                u.DoB, 
                u.Address, 
                w.PicURL
            FROM "WORKER" w
            JOIN "USER" u ON w.Id = u.Id
            WHERE w.Id = %s
        """, [worker_id])
        worker = cursor.fetchone()

        if not worker:
            return render(request, '404.html', {'error': 'Worker not found.'})

    worker_data = {
        'name': worker[0],
        'rate': worker[1],
        'finished_orders': worker[2],
        'phone': worker[3],
        'birth_date': worker[4],
        'address': worker[5],
        'image': worker[6],
    }

    return render(request, 'worker_profile.html', {'worker': worker_data})


@csrf_exempt
@login_required
def cancel_order(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        order_id = body.get('order_id')

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Id
                FROM "ORDER_STATUS"
                WHERE Status = 'Order Cancelled'
            """)
            cancelled_status_id = cursor.fetchone()

            cursor.execute("""
                INSERT INTO "TR_ORDER_STATUS" (serviceTrId, statusId, date)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
            """, [order_id, cancelled_status_id[0]])

        return JsonResponse({'success': True, 'message': 'Order cancelled.'})



