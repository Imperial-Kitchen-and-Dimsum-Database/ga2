from django.shortcuts import render
from django.db import connection
from decimal import Decimal
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import connection
import json
from django.db import DatabaseError
from django.db import transaction
import logging
import traceback
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

def mypay_dashboard(request):
    phone_number = request.session.get('phone_number') or request.COOKIES.get('phone_number')
    
    with connection.cursor() as cursor:
        # Get user data
        cursor.execute("""
            SELECT id, mypaybalance FROM "USER" 
            WHERE phonenum = %s
        """, [phone_number])
        user_data = cursor.fetchone()
        user_id = user_data[0]
        current_balance = user_data[1]
        
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM "WORKER" 
                WHERE id = %s
            )
        """, [user_id])
        is_worker = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT 
                "TR_MYPAY".date,
                "TR_MYPAY_CATEGORY".name as description,
                "TR_MYPAY".nominal as amount
            FROM "TR_MYPAY"
            LEFT JOIN "TR_MYPAY_CATEGORY" 
                ON "TR_MYPAY".categoryid = "TR_MYPAY_CATEGORY".id
            WHERE "TR_MYPAY".userid = %s
            ORDER BY "TR_MYPAY".date DESC
            LIMIT 10
        """, [user_id])
        
        columns = [col[0] for col in cursor.description]
        transactions = []
        
        for row in cursor.fetchall():
            transaction = dict(zip(columns, row))
            transaction['date'] = transaction['date'].strftime('%Y-%m-%d')
            transaction['amount'] = f"${transaction['amount']:,.2f}"
            transactions.append(transaction)
            
    context = {
        'transactions': transactions,
        'current_balance': current_balance,
        'is_worker': is_worker,  # Add this to context
    }
    return render(request, 'mypay.html', context)

def all_transactions(request):
    phone_number = request.session.get('phone_number') or request.COOKIES.get('phone_number')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, mypaybalance FROM "USER" 
            WHERE phonenum = %s
        """, [phone_number])
        user_data = cursor.fetchone()
        user_id = user_data[0]
        current_balance = user_data[1]
        
        cursor.execute("""
            SELECT 
                "TR_MYPAY".date,
                "TR_MYPAY_CATEGORY".name as description,
                "TR_MYPAY".nominal as amount
            FROM "TR_MYPAY"
            LEFT JOIN "TR_MYPAY_CATEGORY" 
                ON "TR_MYPAY".categoryid = "TR_MYPAY_CATEGORY".id
            WHERE "TR_MYPAY".userid = %s
            ORDER BY "TR_MYPAY".date DESC
        """, [user_id])
        
        columns = [col[0] for col in cursor.description]
        transactions = []
        
        for row in cursor.fetchall():
            transaction = dict(zip(columns, row))
            transaction['date'] = transaction['date'].strftime('%Y-%m-%d')
            transaction['amount'] = f"${transaction['amount']:,.2f}"
            transactions.append(transaction)
            
    context = {
        'transactions': transactions,
        'current_balance': current_balance,
    }
    return render(request, 'transactions.html', context)

@csrf_exempt
@require_POST
def transfer_money(request):
    try:
        logger.debug(f"Received transfer request body: {request.body}")
        
        if not request.body:
            return JsonResponse({
                'success': False,
                'message': 'Empty request body'
            }, status=400)

        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON format'
            }, status=400)

        sender_phone = request.session.get('phone_number') or request.COOKIES.get('phone_number')
        if not sender_phone:
            raise ValueError("Sender not authenticated")

        phone = data.get('phone')
        amount = float(data.get('amount', 0))

        if not phone:
            raise ValueError("Recipient phone number is required")
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        if phone == sender_phone:
            raise ValueError("Cannot transfer to your own account")

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, mypaybalance FROM "USER" WHERE phonenum = %s
                """, [sender_phone])
                sender_data = cursor.fetchone()
                if not sender_data:
                    raise ValueError("Sender not found")
                sender_id, sender_balance = sender_data

                if sender_balance < amount:
                    raise ValueError("Insufficient balance")

                cursor.execute("""
                    SELECT id FROM "USER" WHERE phonenum = %s
                """, [phone])
                recipient_data = cursor.fetchone()
                if not recipient_data:
                    raise ValueError("Recipient not found")
                recipient_id = recipient_data[0]

                cursor.execute("""
                    UPDATE "USER" SET mypaybalance = mypaybalance - %s WHERE id = %s
                """, [amount, sender_id])
                cursor.execute("""
                    UPDATE "USER" SET mypaybalance = mypaybalance + %s WHERE id = %s
                """, [amount, recipient_id])

                cursor.execute("""
                    SELECT id FROM "TR_MYPAY_CATEGORY" WHERE name = 'Transfer MyPay to another user'
                """)
                category_id = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO "TR_MYPAY" (id, userid, categoryid, nominal, date)
                    VALUES (%s, %s, %s::uuid, %s, CURRENT_TIMESTAMP)
                """, [uuid.uuid4(), sender_id, category_id, -amount])
                cursor.execute("""
                    INSERT INTO "TR_MYPAY" (id, userid, categoryid, nominal, date)
                    VALUES (%s, %s, %s::uuid, %s, CURRENT_TIMESTAMP)
                """, [uuid.uuid4(), recipient_id, category_id, amount])

        return JsonResponse({
            'success': True,
            'message': 'Transfer successful'
        })

    except ValueError as e:
        logger.error(f"Transfer error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Transfer error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f"Transfer failed: {str(e)}"
        }, status=500)

@require_http_methods(["POST"])
def topup_balance(request):
    try:
        logger.debug(f"Received topup request body: {request.body}")
        
        if not request.body:
            return JsonResponse({
                'success': False,
                'message': 'Empty request body'
            }, status=400)

        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON format'
            }, status=400)

        phone = request.session.get('phone_number') or request.COOKIES.get('phone_number')
        if not phone:
            raise ValueError("User not authenticated")

        amount = float(data.get('amount', 0))
        if amount <= 0:
            raise ValueError("Top-up amount must be positive")

        with transaction.atomic():
            with connection.cursor() as cursor:
                # Get user data including balance
                cursor.execute("""
                    SELECT id, mypaybalance FROM "USER" WHERE phonenum = %s
                """, [phone])
                user_data = cursor.fetchone()
                if not user_data:
                    raise ValueError("User not found")
                user_id = user_data[0]

                # Update balance
                cursor.execute("""
                    UPDATE "USER" SET mypaybalance = mypaybalance + %s 
                    WHERE id = %s
                    RETURNING mypaybalance
                """, [amount, user_id])
                new_balance = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT id FROM "TR_MYPAY_CATEGORY" WHERE name = 'Topup MyPay'
                """)
                category_id = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO "TR_MYPAY" (id, userid, categoryid, nominal, date)
                    VALUES (%s, %s, %s::uuid, %s, CURRENT_TIMESTAMP)
                """, [uuid.uuid4(), user_id, category_id, amount])

        return JsonResponse({
            'success': True,
            'message': 'Top-up successful',
            'new_balance': float(new_balance)
        })

    except ValueError as e:
        logger.error(f"Top-up error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Top-up error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f"Top-up failed: {str(e)}"
        }, status=500)