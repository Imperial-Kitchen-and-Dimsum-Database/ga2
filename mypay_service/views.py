from django.shortcuts import render
from django.db import connection
from decimal import Decimal
from datetime import datetime

def mypay_dashboard(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                "TR_MYPAY".date,
                "TR_MYPAY_CATEGORY".name as description,
                "TR_MYPAY".nominal as amount
            FROM "TR_MYPAY"
            LEFT JOIN "TR_MYPAY_CATEGORY" 
                ON "TR_MYPAY".categoryid = "TR_MYPAY_CATEGORY".id
            ORDER BY "TR_MYPAY".date DESC
            LIMIT 10
        """)
        
        columns = [col[0] for col in cursor.description]
        transactions = []
        
        for row in cursor.fetchall():
            transaction = dict(zip(columns, row))
            transaction['date'] = transaction['date'].strftime('%Y-%m-%d')
            transaction['amount'] = f"${transaction['amount']:,.2f}"
            transactions.append(transaction)
            
    context = {
        'transactions': transactions,
    }
    return render(request, 'mypay.html', context)