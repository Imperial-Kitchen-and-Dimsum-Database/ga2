
from django.shortcuts import render

def mypay_dashboard(request):
    transactions = [
        {'date': '2023-10-01', 'description': 'Cleaning category', 'amount': '$150.00'},
        {'date': '2023-09-28', 'description': 'Cleaning category', 'amount': '$75.00'},
        {'date': '2023-09-25', 'description': 'Deposit', 'amount': '$3,000.00'},
    ]
    context = {
        'transactions': transactions,
    }
    return render(request, 'mypay.html', context)