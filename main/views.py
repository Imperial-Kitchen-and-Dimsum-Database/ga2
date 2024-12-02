from django.shortcuts import render
from functools import wraps
from django.shortcuts import redirect

from functools import wraps
from django.shortcuts import redirect

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
    context = {
        'name': "Database Assignment",
        'services': [
            {
                'category': 'home-cleaning',
                'title': 'Home Cleaning',
                'subcategories': ['Daily Cleaning', 'Ironing']
            },
            {
                'category': 'deep-cleaning',
                'title': 'Deep Cleaning',
                'subcategories': ['Floor and Carpet Cleaning', 'Bathroom and Tile Cleaning']
            },
            {
                'category': 'air-conditioning',
                'title': 'Air Conditioning Service',
                'subcategories': ['Filter Replacement', 'Full AC Maintenance']
            },
            {
                'category': 'massage',
                'title': 'Massage',
                'subcategories': ['Hot Stone Massage', 'Aromatherapy Massage']
            },
            {
                'category': 'haircare',
                'title': 'Haircare',
                'subcategories': ['Haircut', 'Hair Coloring']
            }
        ]
    }
    return render(request, "main.html", context)

def service(request):
    return render(request, "service_details.html")

def subcategory_page(request):
    context = {
        'sessions': [
            {'name': 'Basic Cleaning', 'duration': 2, 'price': 50},
            {'name': 'Deep Cleaning', 'duration': 4, 'price': 90},
            {'name': 'Premium Cleaning', 'duration': 6, 'price': 130},
        ],
        'workers': [
            {'id': '1', 'name': 'John Doe', 'experience': 5, 'image': '../static/image/person.png'},
            {'id': '2', 'name': 'Jane Smith', 'experience': 3, 'image': '../static/image/person.png'},
            {'id': '3', 'name': 'Mike Johnson', 'experience': 7, 'image': '../static/image/person.png'},
            {'id': '4', 'name': 'Sarah Williams', 'experience': 4, 'image': '../static/image/person.png'},
        ]
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

@login_required(login_url='/auth/hero/')
@login_required(login_url='/auth/hero/')
def user_service_bookings(request):
    context = {
        'orders': [
            {
                'order_id': '001',
                'service_name': 'Home Cleaning - Basic Cleaning',
                'order_status': 'Waiting for Payment',
                'order_date': '2024-01-15',
                'total_payment': 50,
                'testimonial_created': False,
                'subcategory': 'Home Cleaning',
            },
            {
                'order_id': '002',
                'service_name': 'Deep Cleaning - Premium Cleaning',
                'order_status': 'Searching for Nearest Workers',
                'order_date': '2024-01-10',
                'total_payment': 130,
                'testimonial_created': False,
                'subcategory': 'Deep Cleaning',
            },
            {
                'order_id': '003',
                'service_name': 'Air Conditioning - Full AC Maintenance',
                'order_status': 'Order Completed',
                'order_date': '2024-01-08',
                'total_payment': 200,
                'testimonial_created': False,
                'subcategory': 'Air Conditioning',
            },
        ],
        'subcategories': ['Home Cleaning', 'Deep Cleaning', 'Air Conditioning'],
        'status_options': ['Waiting for Payment', 'Searching for Nearest Workers', 'Order Completed'],
    }
    return render(request, 'user_service_bookings.html', context)


def worker_profile(request, worker_id):
    workers_data = {
        1: {
            'name': 'John Doe',
            'rate': 9.5,
            'finished_orders': 25,
            'phone': '123-456-7890',
            'birth_date': '1990-05-20',
            'address': '123 Main St, Springfield',
            'image': '/static/image/person.png',
        },
        2: {
            'name': 'Jane Smith',
            'rate': 8.7,
            'finished_orders': 18,
            'phone': '987-654-3210',
            'birth_date': '1995-07-12',
            'address': '456 Oak Ave, Gotham',
            'image': '/static/image/person.png',
        },
        3: {
            'name': 'Mike Johnson',
            'rate': 9.2,
            'finished_orders': 30,
            'phone': '555-333-2222',
            'birth_date': '1988-03-10',
            'address': '789 Pine Rd, Metropolis',
            'image': '/static/image/person.png',
        },
        4: {
            'name': 'Sarah Williams',
            'rate': 8.9,
            'finished_orders': 20,
            'phone': '444-666-1111',
            'birth_date': '1992-08-15',
            'address': '321 Elm St, Star City',
            'image': '/static/image/person.png',
        },
    }

    worker = workers_data.get(worker_id, None)

    if worker:
        context = {'worker': worker}
        return render(request, 'worker_profile.html', context)
    else:
        return render(request, '404.html')
