from django.shortcuts import render
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db import connection


def vouchers(request):
    # Fetch vouchers
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM "VOUCHER" NATURAL JOIN "DISCOUNT"
        """)
        vouchers = cursor.fetchall()

    vouchers_list = []
    for row in vouchers:
        vouchers_list.append({
            'voucher_code': row[0],
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

# def purchase_voucher(request, voucher_id):
#     user_id = request.session.get('user_id')  # Assuming session stores user_id
#     with connection.cursor() as cursor:
#         # Check user MyPay balance
#         cursor.execute('SELECT balance FROM mypay WHERE user_id = %s', [user_id])
#         balance = cursor.fetchone()[0]

#         # Get voucher details
#         cursor.execute("SELECT id, code, discount_percentage FROM vouchers WHERE id = %s", [voucher_id])
#         voucher = cursor.fetchone()
#         if not voucher:
#             return JsonResponse({'error': 'Voucher not found'}, status=404)

#         # Validate balance and process purchase
#         voucher_price = 100  # Example static price for vouchers
#         if balance < voucher_price:
#             return JsonResponse({'error': 'Insufficient balance'}, status=400)
        
#         cursor.execute("UPDATE mypay SET balance = balance - %s WHERE user_id = %s", [voucher_price, user_id])
#         cursor.execute("INSERT INTO user_vouchers (user_id, voucher_id) VALUES (%s, %s)", [user_id, voucher_id])

#     return JsonResponse({'message': 'Voucher purchased successfully'})

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
