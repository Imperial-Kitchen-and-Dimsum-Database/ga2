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
