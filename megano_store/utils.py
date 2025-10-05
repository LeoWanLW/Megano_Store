
import functools
import json
from datetime import datetime, timezone
from os.path import join as join_path
from sqlite3 import DatabaseError

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import JsonResponse

from api_product.models import Product
from megano_store.settings import DEBUG, DEBUG_DIR

User = get_user_model()


def get_user_fullname(user_obj: User) -> str:
    """
    It composes the user full name from fields of normal user`s model Django.
    :param user_obj: instance of User
    :return: composed full name of 'user_obj'
    """
    user_fullname = user_obj.first_name + " " + user_obj.last_name
    if len(user_fullname) > 1:
        user_fullname.strip()
    else:
        user_fullname = user_obj.username + " (nickname)"
    return user_fullname


def format_queryset_to_list(products: QuerySet, count_for_cart_order=None) -> list:
    """
    Format gotten Product`s queryset to list of dictionary,
    if <count_for_cart_order> parameter is present,
    then result is returned for: basket or order (another count of products).
    :param products: queryset of products (many)
    :param count_for_cart_order: count of products (dictionary - {id: quantity})
    :return: list of dictionary (SHORT description of product)
    """
    products_list = []

    for product in products:

        images_list = []
        for item in product.images.all():
            images_list.append({"src": item.image.url if item.image else "",
                                "alt": item.description})
        tags_list = []
        for item in product.tags.all():
            tags_list.append({"id": item.pk, "name": item.value})

        data = {
            "id": product.pk,
            "category": product.category.pk,
            "title": product.title,
            "description": product.description_short,
            "price": product.price,
            "freeDelivery": product.free_delivery,
            "date": product.created_at,
            "rating": product.rating,
            "images": images_list,
            "tags": tags_list,
            "reviews": product.reviews_count
            # field <reviews_count> must be added to products queryset:
            # products = products.annotate(reviews_count=Count("reviews"))
        }
        if isinstance(count_for_cart_order, dict):
            data["count"] = count_for_cart_order[str(product.pk)]
            # find required product and its quantity in <count_for_cart_order>
        else:
            data["count"] = product.count

        products_list.append(data)

    return products_list


def format_instance_to_dict(product: Product) -> dict:
    """
    Format gotten product to dictionary.
    :param product: instance of Product
    :return: dictionary (FULL description of product)
    """
    images_list = []
    for item in product.images.all():
        images_list.append({"src": item.image.url if item.image else "",
                            "alt": item.description})
    tags_list = []
    for item in product.tags.all():
        tags_list.append({"id": item.pk, "name": item.value})

    specs_list = []
    for item in product.specs.all():
        specs_list.append({"name": item.parameter,
                           "value": item.value})
    reviews_list = []
    for item in product.reviews.all():
        reviews_list.append({
            "author": get_user_fullname(item.user),
            "email": item.user.email,
            "text": item.text,
            "rate": item.rate,
            "date": item.created_at.strftime("%Y %B %d, %H:%M, %Z"),
        })

    data = {
        "id": product.pk,
        "category": product.category.pk,
        "title": product.title,
        "description": product.description_short,
        "count": product.count,
        "price": product.price,
        "freeDelivery": product.free_delivery,
        "date": product.created_at,
        "rating": product.rating,
        "images": images_list,
        "tags": tags_list,
        "specifications": specs_list,
        "reviews": reviews_list,
        "fullDescription": product.description_full
    }
    return data


def write_errors(errors: dict, file_name: str) -> None:
    """
    This function is used to write errors into file:
    - 'errors_from_exc.log' - for arisen built-in and sqlite3 exceptions;
    - 'errors_from_if.log' - for errors, what are defined into 'if-else' statement.
    :param errors: dictionary of errors;
    :param file_name: string - name of log file;
    :return: None.
    """
    path_full = join_path(DEBUG_DIR, file_name)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d, %H:%M, %Z")

    with open(path_full, mode="a", encoding="utf-8") as logfile:
        logfile.write("\n" + timestamp + "\n")
        json.dump(errors, logfile, ensure_ascii=False, indent=4)
        logfile.write("\n")


def exception_handler(func):
    """
    This decorator is handler of arisen built-in and sqlite3 exceptions,
    it collects and writes errors to the file 'errors_from_exc.log' in JSON format.
    :param func: function from <views.py>
    :return:
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        try:
            return func(*args, **kwargs)

        except Exception as exc:

            errors = {}

            if isinstance(exc, ValidationError):
                for j, item in enumerate(exc, start=1):
                    errors["Password_Error_" + str(j)] = item
                status = 400

            elif isinstance(exc, json.JSONDecodeError):
                errors["JSON_Error"] = str(exc)
                status = 400

            elif isinstance(exc, (AttributeError, TypeError)):
                errors["Data_Error"] = type(exc).__name__ + " : " + str(exc)
                status = 400

            elif isinstance(exc, ValueError):
                errors["AssignValue_Error"] = type(exc).__name__ + " : " + str(exc)
                status = 400

            elif isinstance(exc, DatabaseError):
                errors["DataBase_Error"] = type(exc).__name__ + " : " + str(exc)
                status = 500

            else:
                errors["Unexpected_Error"] = type(exc).__name__ + " : " + str(exc)
                status = 500

            write_errors(errors, "errors_from_exc.log")

            return JsonResponse(errors, status=status)

    return wrapper


def apply_exception_handler(func):
    if DEBUG:
        return func
    else:
        return exception_handler(func)

