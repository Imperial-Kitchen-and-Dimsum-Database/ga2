from django.shortcuts import render
from functools import wraps
from django.shortcuts import redirect
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_POST

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
    print(f"user id: {user_id}")

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

        has_joined = False  
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
    user_id = request.COOKIES.get('user_id')  # Using cookie for user ID
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tso.Id, 
                   tso.orderDate, 
                   tso.TotalPrice, 
                   ssc.SubcategoryName, 
                   ss.Session, 
                   os.Status AS order_status
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

