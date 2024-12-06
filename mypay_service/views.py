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
        
        cursor.execute("""
            WITH LatestStatus AS (
                SELECT 
                    serviceTrId,
                    statusId,
                    date,
                    ROW_NUMBER() OVER (PARTITION BY serviceTrId ORDER BY date DESC) as rn
                FROM "TR_ORDER_STATUS"
            )
            SELECT 
                tso.Id as id,
                ssc.SubcategoryName as service_name,
                tso.TotalPrice as price,
                tso.orderDate as dateservice,
                w.Id as worker_id
            FROM "TR_SERVICE_ORDER" tso
            LEFT JOIN "SERVICE_SESSION" ss ON tso.serviceCategoryId = ss.SubcategoryId 
                AND tso.Session = ss.Session
            LEFT JOIN "SERVICE_SUBCATEGORY" ssc ON ss.SubcategoryId = ssc.Id
            LEFT JOIN "WORKER" w ON tso.workerId = w.Id
            JOIN LatestStatus ls ON tso.Id = ls.serviceTrId AND ls.rn = 1
            JOIN "ORDER_STATUS" os ON ls.statusId = os.id
            WHERE tso.customerId = %s 
            AND os.Status = 'Waiting for Payment'
            ORDER BY tso.orderDate DESC
        """, [user_id])
        
        columns = [col[0] for col in cursor.description]
        unpaid_orders = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Debug logging
        logger.debug(f"Unpaid orders found: {len(unpaid_orders)}")
        logger.debug(f"User ID: {user_id}")
            
    context = {
        'transactions': transactions,
        'current_balance': current_balance,
        'is_worker': is_worker,  # Add this to context
        'unpaid_orders': unpaid_orders,  # Add unpaid orders to context
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

@csrf_exempt 
@require_http_methods(["POST"])
def withdraw_balance(request):
    try:
        if not request.body:
            return JsonResponse({'success': False, 'message': 'Empty request body'}, status=400)

        data = json.loads(request.body.decode('utf-8'))
        phone = request.session.get('phone_number') or request.COOKIES.get('phone_number')
        
        if not phone:
            raise ValueError("User not authenticated")

        bank_name = data.get('bank_name')
        account_number = data.get('account_number')
        amount = float(data.get('amount', 0))

        if not all([bank_name, account_number]):
            raise ValueError("Bank details are required")
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        with transaction.atomic():
            with connection.cursor() as cursor:
                # Get user data and check if worker
                cursor.execute("""
                    SELECT u.id, u.mypaybalance, EXISTS(
                        SELECT 1 FROM "WORKER" w WHERE w.id = u.id
                    ) as is_worker
                    FROM "USER" u WHERE u.phonenum = %s
                """, [phone])
                user_data = cursor.fetchone()
                
                if not user_data:
                    raise ValueError("User not found")
                    
                user_id, current_balance, is_worker = user_data
                
                if not is_worker:
                    raise ValueError("Only workers can withdraw funds")
                if current_balance < amount:
                    raise ValueError("Insufficient balance")

                # Update user balance
                cursor.execute("""
                    UPDATE "USER" SET mypaybalance = mypaybalance - %s 
                    WHERE id = %s
                    RETURNING mypaybalance
                """, [amount, user_id])
                new_balance = cursor.fetchone()[0]

                # Get withdrawal category ID
                cursor.execute("""
                    SELECT id FROM "TR_MYPAY_CATEGORY" 
                    WHERE name = 'Withdrawal MyPay to bank account'
                """)
                category_id = cursor.fetchone()[0]

                # Record transaction
                cursor.execute("""
                    INSERT INTO "TR_MYPAY" (id, userid, categoryid, nominal, date)
                    VALUES (%s, %s, %s::uuid, %s, CURRENT_TIMESTAMP)
                """, [uuid.uuid4(), user_id, category_id, -amount])

        return JsonResponse({
            'success': True,
            'message': 'Withdrawal successful',
            'new_balance': float(new_balance)
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Withdrawal error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f"Withdrawal failed: {str(e)}"
        }, status=500)

@csrf_exempt
@require_POST
def pay_service(request):
    try:
        if not request.body:
            return JsonResponse({'success': False, 'message': 'Empty request body'}, status=400)

        data = json.loads(request.body.decode('utf-8'))
        phone = request.session.get('phone_number') or request.COOKIES.get('phone_number')
        
        logger.debug(f"Processing payment request for phone: {phone}")
        
        if not phone:
            raise ValueError("User not authenticated")

        order_id = data.get('order_id')
        amount = float(data.get('amount', 0))

        if not order_id:
            raise ValueError("Order ID is required")
        if amount <= 0:
            raise ValueError("Payment amount must be positive")

        with transaction.atomic():
            with connection.cursor() as cursor:
                # Get user data and check balance
                cursor.execute("""
                    SELECT id, mypaybalance 
                    FROM "USER" 
                    WHERE phonenum = %s
                """, [phone])
                user_data = cursor.fetchone()
                
                if not user_data:
                    logger.error(f"User not found for phone: {phone}")
                    raise ValueError("User not found")
                    
                user_id, current_balance = user_data
                logger.debug(f"User found: {user_id}, balance: {current_balance}")
                
                if current_balance < amount:
                    raise ValueError("Insufficient balance")

                # Get order details and verify
                cursor.execute("""
                    SELECT so.customerId, so.workerId, so.totalPrice 
                    FROM "TR_SERVICE_ORDER" so
                    JOIN "TR_ORDER_STATUS" tos ON so.id = tos.serviceTrId
                    JOIN "ORDER_STATUS" os ON tos.statusId = os.id
                    WHERE so.id = %s AND os.status = 'Waiting for Payment'
                """, [order_id])
                order_data = cursor.fetchone()
                
                if not order_data:
                    logger.error(f"Order not found or not in waiting status: {order_id}")
                    raise ValueError("Order not found or already paid")
                
                customer_id, worker_id, total_price = order_data
                
                if customer_id != user_id:
                    raise ValueError("Unauthorized to pay this order")
                if float(total_price) != amount:
                    raise ValueError("Payment amount does not match order total")

                # Update user balance
                cursor.execute("""
                    UPDATE "USER" 
                    SET mypaybalance = mypaybalance - %s 
                    WHERE id = %s
                """, [amount, user_id])

                # Update worker balance
                cursor.execute("""
                    UPDATE "USER" 
                    SET mypaybalance = mypaybalance + %s 
                    WHERE id = %s
                """, [amount, worker_id])

                # Get payment category ID
                cursor.execute("""
                    SELECT id FROM "TR_MYPAY_CATEGORY" 
                    WHERE name = 'Pay for service transaction'
                """)
                category_data = cursor.fetchone()
                if not category_data:
                    raise ValueError("Payment category not found")
                category_id = category_data[0]

                # Record transactions
                payment_id = uuid.uuid4()
                cursor.execute("""
                    INSERT INTO "TR_MYPAY" (id, userid, categoryid, nominal, date)
                    VALUES (%s, %s, %s::uuid, %s, CURRENT_TIMESTAMP)
                """, [payment_id, user_id, category_id, -amount])
                
                cursor.execute("""
                    INSERT INTO "TR_MYPAY" (id, userid, categoryid, nominal, date)
                    VALUES (%s, %s, %s::uuid, %s, CURRENT_TIMESTAMP)
                """, [uuid.uuid4(), worker_id, category_id, amount])

                # Get paid status ID
                cursor.execute("""
                    SELECT id FROM "ORDER_STATUS" WHERE status = 'Order Completed'
                """)
                status_data = cursor.fetchone()
                if not status_data:
                    raise ValueError("Paid status not found")

                # Update order status to paid
                cursor.execute("""
                    INSERT INTO "TR_ORDER_STATUS" (servicetrid, statusid, date)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                """, [order_id, status_data[0]])

        return JsonResponse({
            'success': True,
            'message': 'Payment successful'
        })

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Payment error: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f"Payment failed: {str(e)}"
        }, status=500)
