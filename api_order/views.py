
import json

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404

from . import cart
from .models import Order, OrderItem
from api_product.models import Product
from megano_store.settings import SESSION_KEY_CART

from megano_store.utils import (apply_exception_handler, write_errors,
                                get_user_fullname, format_queryset_to_list)

User = get_user_model()


@apply_exception_handler
def get_basket_view(request: HttpRequest) -> JsonResponse:
    """
    See file cart.py (this catalog).
    :param request: HttpRequest
    :return: list of products for frontend (SHORT description of product)
    """
    if request.method == "GET":
        basket = cart.get_cart(request)
        return JsonResponse(basket, safe=False, status=200)

    elif request.method == "POST":
        basket = cart.add_or_remove_session_cart(request, 1)
        return JsonResponse(basket, safe=False, status=200)  # status?

    elif request.method == "DELETE":
        basket = cart.add_or_remove_session_cart(request, 0)
        return JsonResponse(basket, safe=False, status=200)  # status?

    return JsonResponse({}, status=400)


def format_order_to_dict(order: Order) -> dict:
    """
    Compose dictionary from order`s data.
    For get list of products used function <format_queryset_to_list> (see <utils.py).
    :param order: instance of model Order
    :return: dictionary of order`s data
    """
    data = {
        "id": order.pk,
        "createdAt": order.created_at.strftime(
            "%Y %B %d, %H:%M, %Z"
        ),
        "status": order.status,
        "deliveryType": order.delivery_type,
        "city": order.delivery_city,
        "address": order.delivery_address,
        "paymentType": order.payment_type,
        "totalCost": order.payment_total_cost,
    }
    if order.user:
        data["fullName"] = get_user_fullname(order.user),
        data["email"] = order.user.email,
        data["phone"] = order.user.profile.phone_number

    order_items = order.orderitems.all()

    if order_items:
        prod_count = {}

        for item in order_items:
            prod_count[str(item.product_id)] = item.quantity

        # products = Product.objects.filter(orderitems__order=order)
        products = Product.objects.filter(id__in=prod_count.keys())
        products = products.annotate(reviews_count=Count("reviews"))

        data["products"] = format_queryset_to_list(products, prod_count)

    return data


@apply_exception_handler
def get_orders_view(request: HttpRequest) -> JsonResponse:
    """
    For current user:
    If method is <GET> - return the list of orders.
    If method is <POST>, create an order from the products passed in request body,
    and calculate its total cost. The following fields are not written:
    <deliveryType>, <city>, <address>, <paymentType>.
    Depending on whether the user is authenticated or not,
    write either <user> field or <session_key> field of model <Order>.
    :param request: HttpRequest (GET - without parameters, POST - list of products).
    :return: GET - list of orders; POST - ID of created order.
    """
    curr_user = request.user

    if request.method == "GET":
        orders_list = []

        if curr_user.is_authenticated:
            orders = Order.objects.filter(user=curr_user)

            if orders:
                for order in orders:
                    orders_list.append(format_order_to_dict(order))

        return JsonResponse(orders_list, safe=False, status=200)

    elif request.method == "POST":

        errors = {}
        order_total_cost = 0
        order_data = {item["id"]: item["count"]
                      for item in json.loads(request.body)}
                      # values of item["id"], item["count"] have type <int>
        is_order_delete = True

        with transaction.atomic():

            if curr_user.is_authenticated:
                order = Order.objects.create(user=curr_user, status="created")
            else:
                order = Order.objects.create(
                    session_key=request.session.session_key,
                    status="created"
                )

            for key, value in order_data.items():
                prod_id_in_order = key
                prod_count_in_order = value

                prod_obj_db = get_object_or_404(Product, pk=prod_id_in_order)

                if prod_count_in_order > 0:
                    prod_count_db = prod_obj_db.count

                    if prod_count_db > 0:
                        if prod_count_in_order > prod_count_db:
                            prod_count_in_order = prod_count_db

                        OrderItem.objects.create(
                            order=order,
                            product=prod_obj_db,
                            quantity=prod_count_in_order
                        )
                        order_total_cost += prod_obj_db.price * prod_count_in_order
                        is_order_delete = False

                    else:
                        errors = {"ValueError(" + str(key) + ")":
                            f"<{prod_obj_db.title}> is not available (count = 0)."}
                        write_errors(errors, "errors_from_if.log")
                else:
                    errors = {"OrderError(" + str(key) + ")":
                        f"Number of <{prod_obj_db.title}> in order is zero."}
                    write_errors(errors, "errors_from_if.log")

            if is_order_delete:
                order.delete()
                return JsonResponse(errors, status=400)

            else:
                order.payment_total_cost = order_total_cost
                order.save()

                request.session[SESSION_KEY_CART] = {}
                request.session.modified = True

                return JsonResponse({"orderId": order.pk}, status=201)

    else:
        errors = {"RequestError":
            f"Request method <{request.method}> is not supported."}
        write_errors(errors, "errors_from_if.log")

        return JsonResponse(errors, status=400)


@apply_exception_handler
def get_one_order_view(request: HttpRequest, **kwargs) -> JsonResponse:
    """
    By order ID (kwargs["pk"]):
    If method is <GET>, return the order.
    If method is <POST>, write delivery and payment fields for order,
    and also if field user is empty - write request user into it.
    :param request: HttpRequest
    :param kwargs: ID of the order from URL pattern
    :return: GET - order (dictionary); POST - order ID.
    """
    #
    order_id = kwargs["pk"]
    one_order = get_object_or_404(Order, pk=order_id)

    if request.method == "GET":
        return JsonResponse(format_order_to_dict(one_order), status=200)

    elif request.method == "POST":
        if not one_order.user:
            one_order.user = request.user
        one_order.status = "pending"

        data = json.loads(request.body)
        one_order.delivery_type = data.get("deliveryType")
        one_order.delivery_city = data.get("city")
        one_order.delivery_address = data.get("address")
        one_order.payment_type = data.get("paymentType")
        one_order.save()

        return JsonResponse({"orderId": order_id}, status=201)

    else:
        errors = {"RequestError":
            f"Request method <{request.method}> is not supported."}
        write_errors(errors, "errors_from_if.log")

        return JsonResponse(errors, status=400)


@apply_exception_handler
def order_payment_view(request: HttpRequest, **kwargs) -> JsonResponse:
    """
    POST request.
    Validate card and payment imitation for order with ID = kwargs["pk"].
    :param request: HttpRequest
    :param kwargs: ID of the order from URL pattern
    :return: JsonResponse (success message or error message)
    """
    data = json.loads(request.body)
    num_str = data.get("number").strip()
    num_int = int(num_str)

    if len(num_str) < 9 and num_int % 10 != 0 and num_int % 2 == 0:

        with transaction.atomic():
            order_id = kwargs["pk"]
            order = get_object_or_404(Order, pk=order_id)
            order.status = "paid"
            order.save()

            for item in order.orderitems.all():
                product = item.product

                if product.count > item.quantity:
                    product.count -= item.quantity
                else:
                    product.count = 0
                    product.available = False
                product.save()

            return JsonResponse(
                {"Message": f"Order № {order_id} has been successfully paid."},
                status=201
                )
    else:
        errors = {"PaymentError": "The card number is incorrect."}
        write_errors(errors, "errors_from_if.log")

        return JsonResponse(errors, status=400)

