from django.shortcuts import render, get_object_or_404

from .models import OrderItem
from cart.cart import Cart
from .forms import *

from django.views.generic.base import View
from django.http import JsonResponse

from django.contrib.admin.views.decorators import staff_member_required


def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'],
                                         quantity=item['quantity'])

            cart.clear()
            return render(request, 'order/created.html', {'order':order})
    else:
        form = OrderCreateForm()
    return render(request, 'order/create.html', {'cart':cart, 'form':form})


def order_complete(request):
    order_id = request.GET.get('order_id')
    order = Order.objects.get(id=order_id)
    return render(request, 'order/created.html', {'order':order})


class OrderCreateAjaxView(View):
    def post(self, request, *args, **kwargs):

        cart = Cart(request)
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'],
                                     quantity=item['quantity'])
            data = {
                "order_id": order.id,
            }
            return JsonResponse(data)
        else:
            return JsonResponse({}, status=401)

from .models import OrderTransaction
class OrderCheckoutAjaxView(View):
    def post(self, request, *args, **kwargs):

        order_id = request.POST.get('order_id')
        order = Order.objects.get(id=order_id)
        amount = request.POST.get('amount')

        try:
            merchant_order_id = OrderTransaction.objects.create_new(order=order, amount=amount)
        except:
            merchant_order_id = None

        if merchant_order_id is not None:
            data = {
                "works": True,
                "merchant_id": merchant_order_id,
            }
            return JsonResponse(data)
        else:
            return JsonResponse({}, status=401)


class OrderImpAjaxView(View):
    def post(self, request, *args, **kwargs):
        order_id = request.POST.get('order_id')
        order = Order.objects.get(pk=order_id)
        merchant_id = request.POST.get('merchant_id')
        imp_id = request.POST.get('imp_id')
        amount = request.POST.get('amount')

        if not order.exists():
            return JsonResponse({}, status=401)

        order = order[0]

        transaction = OrderTransaction.objects.filter(order=order, merchant_order_id=merchant_id, amount=amount)

        if not transaction.exists():
            return JsonResponse({}, status=401)

        # 결제 정보 수정
        try:
            exact_transaction = transaction[0]
            exact_transaction.transaction_id = imp_id
            exact_transaction.success = True
            exact_transaction.save()

            # 주문 정보 - 결제 완료로 변경
            order.paid = True
            order.save()
            data = {
                'works': True
            }

            cart = Cart(request)
            cart.clear()

            return JsonResponse(data)
        except Exception as e:
            print("transaction error", e)
            return JsonResponse({"message": str(e)}, status=401)

@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id= order_id)
    return render(request, 'order/admin/detail.html', {'order':order})
