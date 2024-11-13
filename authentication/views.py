from django.shortcuts import render

# Create your views here.
def temp_hero(request):
    return render(request, "hero.html")
