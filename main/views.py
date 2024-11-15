from django.shortcuts import render

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
            {'name': 'John Doe', 'experience': 5, 'image': '../static/image/person.png'},
            {'name': 'Jane Smith', 'experience': 3, 'image': '../static/image/person.png'},
            {'name': 'Mike Johnson', 'experience': 7, 'image': '../static/image/person.png'},
            {'name': 'Sarah Williams', 'experience': 4, 'image': '../static/image/person.png'},
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
