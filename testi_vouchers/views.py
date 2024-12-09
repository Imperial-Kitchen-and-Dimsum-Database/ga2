import datetime
import uuid
from django.shortcuts import redirect, render
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
import json


def voucher(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM "VOUCHER" NATURAL JOIN "DISCOUNT"
        """)
        vouchers = cursor.fetchall()

    vouchers_list = []
    for row in vouchers:
        vouchers_list.append({
            'code': row[0],
            'discount_percentage': row[4],
            'service_name': "SERVICES",
            'minimum_transaction': row[5],
            'valid_days': row[1],
            'user_quota': row[2],
            'price': row[1],
        })

    # Fetch promos
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM "PROMO" NATURAL JOIN "DISCOUNT"
        """)
        promos = cursor.fetchall()

    promos_list = []
    for row in promos:
        promos_list.append({
            'date': row[1],
            'code': row[0],
            'discount': row[2],
            'min_transaction': row[3],
        })

    # Paginate vouchers
    paginator = Paginator(vouchers_list, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'vouchers.html', {'page_obj': page_obj, 'promos_list': promos_list})




@csrf_protect
def purchase_voucher(request):
    user_id = request.COOKIES.get('user_id')
    print(f"user id: {user_id}")

    voucher_code = request.POST.get('code')
    print(voucher_code)

    with connection.cursor() as cursor:
            
            cursor.execute("""
                SELECT "mypaybalance" FROM "USER" WHERE "id" = %s
            """, [user_id])
            balance = cursor.fetchone()[0]
            print(f"Balance Result: {balance}")  

            cursor.execute("""
                SELECT * FROM "VOUCHER" WHERE "code" = %s
            """, [voucher_code])
            voucher = cursor.fetchone()
            print(f"Voucher Result: {voucher}")

            cursor.execute("""
                SELECT "price" FROM "VOUCHER" WHERE "code" = %s
            """, [voucher_code])
            voucher_price = cursor.fetchone()[0]
            print(f"Voucher Price: {voucher_price}")  


            if balance >= voucher_price:
                    
                    new_balance = balance - voucher_price
                    cursor.execute("""
                    UPDATE "USER" SET "mypaybalance" = %s WHERE "id" = %s
                    """, [new_balance, user_id])
                    print(f"Balance Updated: {new_balance}")

                    tr_pv_id = uuid.uuid4()
                    mypay = '3ddee865-2af9-4188-b2f9-7d601a325ea9'
                    purchase_date = datetime.datetime.now()
                    expiration_date = purchase_date + datetime.timedelta(days=voucher[1] + 30)
                    print(f"Expiration date is {expiration_date}")
                    voucher_uses = voucher[2]
                    print(f"Voucher uses is {voucher_uses}")

                    cursor.execute("""  
                    INSERT INTO "TR_VOUCHER_PAYMENT" VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [tr_pv_id, purchase_date, expiration_date, voucher_uses, user_id, voucher_code, mypay])

                    context = {
                        'voucher_code': voucher_code,
                        'voucher_uses': voucher_uses,
                        'valid_until': expiration_date,       
                    }

                    return render(request, 'success.html', context)
                    # return render(request, 'success.html')
            
            else:
                return render(request, 'failure.html')

# def view_testimonials(request, service_id):
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             SELECT t.rating, t.comment, u.name 
#             FROM testimonials t 
#             JOIN users u ON t.user_id = u.id 
#             WHERE t.service_id = %s
#         """, [service_id])
#         testimonials = cursor.fetchall()
#     return render(request, 'view_testimonials.html', {'testimonials': testimonials})


# @csrf_exempt
# def add_testimonial(request):
#     if request.method == 'POST':
#         user_id = request.session.get('user_id')
#         service_id = request.POST.get('service_id')
#         rating = request.POST.get('rating')
#         comment = request.POST.get('comment')

#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 INSERT INTO testimonials (user_id, service_id, rating, comment) 
#                 VALUES (%s, %s, %s, %s)
#             """, [user_id, service_id, rating, comment])

#         return JsonResponse({'message': 'Testimonial added successfully'})
#     return JsonResponse({'error': 'Invalid request'}, status=400)


