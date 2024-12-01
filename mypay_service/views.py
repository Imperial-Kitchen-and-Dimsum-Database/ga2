from django.shortcuts import render
from django.db import connection
from decimal import Decimal
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import connection
import json

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




@require_POST
@login_required
def transfer_money(request):
    try:
        data = json.loads(request.body)
        receiver_phone = data.get('phone')
        amount = float(data.get('amount'))

        # Get receiver ID from phone
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id FROM "TR_USER" WHERE phone = %s
            """, [receiver_phone])
            result = cursor.fetchone()
            if not result:
                return JsonResponse({
                    'success': False, 
                    'message': 'Recipient not found'
                })
            receiver_id = result[0]

        # Execute transfer
        with connection.cursor() as cursor:
            cursor.execute("""
                CALL transfer_mypay_balance(%s, %s, %s, 0, 0)
            """, [request.user.id, receiver_id, amount])
            
            # Get updated balance
            cursor.execute("""
                SELECT balance FROM "TR_MYPAY_BALANCE" 
                WHERE userid = %s
            """, [request.user.id])
            new_balance = cursor.fetchone()[0]

        return JsonResponse({
            'success': True,
            'new_balance': new_balance,
            'message': 'Transfer successful'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
    
@require_POST
@login_required
def topup_balance(request):
    try:
        data = json.loads(request.body)
        amount = float(data.get('amount'))

        with connection.cursor() as cursor:
            cursor.execute("""
                CALL topup_mypay_balance(%s, %s, 0)
            """, [request.user.id, amount])
            
            cursor.execute("""
                SELECT balance FROM "TR_MYPAY_BALANCE" 
                WHERE userid = %s
            """, [request.user.id])
            new_balance = cursor.fetchone()[0]

        return JsonResponse({
            'success': True,
            'new_balance': new_balance,
            'message': 'Top-up successful'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })