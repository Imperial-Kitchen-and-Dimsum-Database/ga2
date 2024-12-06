from django.shortcuts import render
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



@csrf_protect
def purchase_voucher(request, voucher_id=None):
    data = json.loads(request.body)
    voucher_id = data.get('code')
    user_id = request.session.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("""
                        SELECT "mypaybalance" FROM "USER" WHERE "id" = %s
                        """, [user_id])
        balance_result = cursor.fetchone()
        balance = balance_result[0]

    return render(request, 'purchase_voucher.html', {'voucher_id': voucher_id, 'balance': balance})


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
