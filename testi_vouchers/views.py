from django.shortcuts import render

def vouchers(request):
    return render(request, "vouchers.html")