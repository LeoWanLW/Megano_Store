
import json

from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpRequest

from api_product.models import Product
from megano_store.settings import SESSION_KEY_CART
from megano_store.utils import format_queryset_to_list
from .models import Cart, CartItem

# if necessary, code of the type:
# products = Product.objects.filter(id__in=my_dict.keys())
# can be replaced with a code of the following type:
# products = Product.objects.filter(id__in=[int(pk) for pk in my_dict.keys()])
# here <str> to <int> conversion is performed


def get_cart(request: HttpRequest) -> list:
    """
    Get basket from the session.
    If it is empty, get basket from the DB, if user is authenticated.
    :param request: HttpRequest
    :return: list of products for frontend (SHORT description of product)
    """
    cart_session = request.session.get(SESSION_KEY_CART, {})

    if cart_session:
        products = Product.objects.filter(id__in=cart_session.keys())
        products = products.annotate(reviews_count=Count("reviews"))

        return format_queryset_to_list(products, cart_session)

    else:
        if request.user.is_authenticated:

            cart_db, _ = Cart.objects.get_or_create(user=request.user)
            cart_items = cart_db.cartitems.all()

            if cart_items:
                prod_count = {}

                for item in cart_items:
                    prod_count[str(item.product_id)] = item.quantity

                products = Product.objects.filter(id__in=prod_count.keys())
                products = products.annotate(reviews_count=Count("reviews"))

                prod_list = format_queryset_to_list(products, prod_count)

                for item in prod_list:
                    cart_session[str(item["id"])] = item["count"]

                request.session[SESSION_KEY_CART] = cart_session
                request.session.modified = True

                return prod_list
    return []


def add_or_remove_session_cart(request: HttpRequest, action: int) -> list:
    """
    Add product to basket or remove product from basket (in session).
    :param request: HttpRequest
    :param action: 1 - add, 0 - remove
    :return: list of products for frontend (SHORT description of product)
    """
    data = json.loads(request.body)
    id = str(data.get("id"))
    count = data.get("count")

    cart_session = request.session.get(SESSION_KEY_CART, {})

    if cart_session:
        if id in cart_session:
            if action == 1:
                cart_session[id] += count
            else:
                cart_session[id] -= count if cart_session[id] >= count else 0
        else:
            if action == 1:
                cart_session[id] = count
    else:
        if action == 1:
            cart_session[id] = count

    request.session[SESSION_KEY_CART] = cart_session
    request.session.modified = True

    products = Product.objects.filter(id__in=cart_session.keys())
    products = products.annotate(reviews_count=Count("reviews"))

    return format_queryset_to_list(products, cart_session)


def save_session_cart_to_db(request: HttpRequest, new_user: User = None) -> None:
    """
    Save basket from session to DB. For new user (parameter <new_user> is not None)
    create instances Cart and CartItem.
    :param request: HttpRequest
    :param new_user: instance of model User
    :return: None
    """
    cart_session = request.session.get(SESSION_KEY_CART, {})

    if not cart_session:
        return

    if new_user is not None:
        cart = Cart.objects.create(user=new_user)
    else:
        cart, _ = Cart.objects.get_or_create(user=request.user)

    for prod_id, quantity in cart_session.items():

        product = Product.objects.get(id=int(prod_id))

        if new_user is not None:
            if quantity > 0:
                CartItem.objects.create(cart=cart, product=product, quantity=quantity)
        else:
            cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product)
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()

    request.session[SESSION_KEY_CART] = {}
    request.session.modified = True


# cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
# if not created:
#     cart_item.quantity += quantity
# else:
#     cart_item.quantity = quantity
# cart_item.save()

