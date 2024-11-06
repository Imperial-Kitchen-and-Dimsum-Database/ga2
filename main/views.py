from django.shortcuts import render


def show_main(request):

    context = {
        'name' : "Database Assignment"
    }

    return render(request, "main.html", context)
