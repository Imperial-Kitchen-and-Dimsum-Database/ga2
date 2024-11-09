from django.shortcuts import render


def show_main(request):
    context = {
        'name' : "Database Assignment"
    }
    return render(request, "main.html", context)

def service(request):
    return render(request, "service_details.html")

def subcategory(request):
    return render(request, "subcategory_page.html")
