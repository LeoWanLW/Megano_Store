
from math import ceil
import json

from django.core.cache import cache
from django.db.models import Count, Prefetch
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404

from megano_store.settings import (DEBUG, CATEGORY_ID, RATING_VALUE,
                                   PRODUCT_LIMIT, PAGE_ITEM_LIMIT)
from megano_store.utils import (apply_exception_handler, get_user_fullname,
                                format_queryset_to_list, format_instance_to_dict)
from .models import (Category, Product, ProductImage, ProductTag, ProductReview, Sale)


def get_categories(sub=True) -> list:
    """
    Get from cache or DB: root categories or subcategories (the same table)
    :param sub: if True - get subcategories else - root categories
    :return: list of dictionary
    """
    cache_key = "subcategories" if sub else "rootcategories"
    categories_list = cache.get(cache_key)

    if categories_list is None:

        if sub:
            categories = Category.objects.exclude(parent=None)
        else:
            categories = Category.objects.filter(parent=None)

        categories = categories.prefetch_related("images")

        categories_list = []

        for category in categories:
            first_image = category.images.first()
            image_data = {"src": "", "alt": ""}

            if first_image:
                image_data["src"] = first_image.image.url
                image_data["alt"] = first_image.description

            category_dict = {"id": category.pk,
                             "title": category.title,
                             "image": image_data}
            if sub:
                category_dict["parent_id"] = category.parent_id
            else:
                category_dict["subcategories"] = []

            categories_list.append(category_dict)

        if not DEBUG:
            cache.set(cache_key, categories_list, 7200)

    return categories_list


@apply_exception_handler
def get_categories_view(request: HttpRequest) -> JsonResponse:
    """
    Invoke func <get_categories> then compose gotten root categories and subcategories
    to list of dictionary for frontend.
    :param request: HttpRequest
    :return: list of dictionary into JsonResponse
    """
    categories_root = get_categories(sub=False)
    categories_sub = get_categories()

    for category_root in categories_root:
        for category_sub in categories_sub:
            if "parent_id" in category_sub.keys():  # do not delete !
                if category_sub["parent_id"] == category_root["id"]:
                    category_sub.pop("parent_id", None)
                    category_root["subcategories"].append(category_sub)

    return JsonResponse(categories_root, safe=False, status=200)


def get_tags(category_id="") -> list:
    """
    Get tags for products of all categories or only selected categories
    (product availability is not taken into account), then create list from them
    :param category_id: id of selected category
    :return: list of tags
    """
    cache_key = "alltags" if category_id=="" else "tagsfor" + category_id
    tags_list = cache.get(cache_key)

    if tags_list is None:

        tags_list = []
        if category_id:
            tags = ProductTag.objects.filter(product__category_id=category_id)
        else:
            tags = ProductTag.objects.all()
        tags = tags.distinct()

        for tag in tags:
            tags_list.append({"id": tag.pk, "name": tag.value})

        if not DEBUG:
            cache.set(cache_key, tags_list, 7200)

    return tags_list


@apply_exception_handler
def get_tags_view(request: HttpRequest) -> JsonResponse:
    """
    Extract all tags (for all categories) or
    tags for selected categories (see function <get_tags> above).
    :param request: HttpRequest
    :return: list of tags
    """

    if "category" in request.GET:
        category_id = request.GET.get("category")
        tags_list = get_tags(category_id=category_id)
    else:
        tags_list = get_tags()

    return JsonResponse(tags_list, safe=False, status=200)


def get_product_list(cache_key: str, **kwargs) -> list:
    """
    To form QuerySet for section "banners", "limited", "popular" and pass it
    to function <format_queryset_to_list> (plus cache)
    :param cache_key: key for cache
    :param kwargs: keyword parameters for query filter
    :return: list of dictionaries
    """
    data = cache.get(cache_key)

    if data is None:

        qs = Product.objects.filter(**kwargs, available=True)[:PRODUCT_LIMIT]

        pref_images = Prefetch("images",
                            queryset=ProductImage.objects.only("image", "description"))

        qs = qs.prefetch_related(pref_images, "tags")

        products = qs.annotate(reviews_count=Count("reviews"))

        data = format_queryset_to_list(products)  # see utils.py

        if not DEBUG:
            cache.set(cache_key, data, 3600)

    return data


@apply_exception_handler
def get_banners_view(request: HttpRequest) -> JsonResponse:
    """
    Make cache key and get bunners for homepage
    (see function <get_product_list> above).
    :param request: HttpRequest
    :return: JsonResponse (list of products)
    """
    cache_key = "banners" + CATEGORY_ID
    data = get_product_list(cache_key, category_id=int(CATEGORY_ID))

    return JsonResponse(data, safe=False, status=200)


@apply_exception_handler
def get_limited_view(request: HttpRequest) -> JsonResponse:
    """
    Make cache key and get limited products for homepage
    (see function <get_product_list> above).
    :param request: HttpRequest
    :return: JsonResponse (list of products)
    """
    cache_key = "limited"
    data = get_product_list(cache_key, limited_edition=True)

    return JsonResponse(data, safe=False, status=200)


@apply_exception_handler
def get_popular_view(request: HttpRequest) -> JsonResponse:
    """
    Make cache key and get popular products for homepage
    (see function <get_product_list> above).
    :param request: HttpRequest
    :return: JsonResponse (list of products)
    """
    cache_key = "popular" + RATING_VALUE
    data = get_product_list(cache_key, rating__gt=int(RATING_VALUE))

    return JsonResponse(data, safe=False, status=200)


@apply_exception_handler
def get_sales_view(request: HttpRequest) -> JsonResponse:
    """
    Get products for sale.
    :param request: HttpRequest
    :return: JsonResponse (list of products and pages)
    """
    page_current = int(request.GET.get("currentPage"))

    cache_key = "sales"
    data = cache.get(cache_key)

    if data is None:
        qs = Sale.objects.all().select_related("product")

        pref_images = Prefetch(
            "product__images",
            queryset=ProductImage.objects.only("image", "description")
        )
        qs = qs.prefetch_related(pref_images)

        data = []
        for sale in qs:
            prod = sale.product

            images_list = []
            for item in prod.images.all():
                images_list.append({"src": item.image.url if item.image else "",
                                    "alt": item.description})
            data.append({
                "id": prod.pk,
                "price": prod.price,
                "salePrice": sale.price_sale,
                "dateFrom": sale.date_from,
                "dateTo": sale.date_to,
                "title": prod.title,
                "images": images_list,
            })
        if not DEBUG:
            cache.set(cache_key, data, 7200)

    count = len(data)
    page_last = ceil(count / PAGE_ITEM_LIMIT)

    products = {"items": data, "currentPage": page_current, "lastPage": page_last}

    return JsonResponse(products, status=200)


@apply_exception_handler
def get_catalog_view(request: HttpRequest) -> JsonResponse:
    """
    Get full catalog or filter and sort catalog of products.
    Data for filter and sort is taken from <query string>.
    :param request: HttpRequest
    :return: JsonResponse
    """
    category = request.GET.get("category")
    search = request.GET.get("filter[name]").strip().lower()
    available = request.GET.get("filter[available]")
    free_delivery = request.GET.get("filter[freeDelivery]")
    price_min = request.GET.get("filter[minPrice]")
    price_max = request.GET.get("filter[maxPrice]")
    sort_item = request.GET.get("sort")
    sort_mode = request.GET.get("sortType")
    tags = request.GET.getlist("tags[]")
    page_current = int(request.GET.get("currentPage"))
    item_limit = int(request.GET.get("limit"))

    cache_key = "".join([search, available, free_delivery, price_min, price_max,
                         sort_item, sort_mode, "".join(sorted(tags))])
    if category is not None:
        cache_key = cache_key + category

    data = cache.get(cache_key)

    if data is None:

        qs = Product.objects.all()

        if category is not None:
            qs = qs.filter(category_id=int(category))

        if available == "true":
            qs = qs.filter(available=True)

        if free_delivery == "true":
            qs = qs.filter(free_delivery=True)

        if search:
            qs = qs.filter(title_low__contains=search)

        if tags:
            qs = qs.filter(tags__id__in=list(map(int, tags)))

        qs = qs.filter(price__gt=int(price_min), price__lte=int(price_max))

        qs = qs.annotate(reviews_count=Count("reviews"))

        if sort_item == "reviews":
            sort_item = "reviews_count"
        elif sort_item == "date":
            sort_item = "created_at"

        if sort_mode == "dec":
            sort_item = "-" + sort_item

        qs = qs.order_by(sort_item)
        qs = qs.distinct()

        pref_images = Prefetch(
            "images",
            queryset=ProductImage.objects.only("image", "description")
        )
        qs = qs.prefetch_related(pref_images, "tags")

        data = format_queryset_to_list(qs)  # see utils.py

        if not DEBUG:
            cache.set(cache_key, data, 3600)

    count = len(data)
    page_last = ceil(count / item_limit)

    products = {"items": data, "currentPage": page_current, "lastPage": page_last}

    return JsonResponse(products, status=200)


@apply_exception_handler
def get_product_view(request: HttpRequest, **kwargs) -> JsonResponse:
    """
    Get FULL description of product (invoke function <format_queryset_to_dict>.
    :param request: HttpRequest
    :param kwargs: <pk> of product from urlpattern
    :return: JsonResponse
    """
    cache_key = "product" + str(kwargs["pk"])
    data = cache.get(cache_key)

    if data is None:

        product = Product.objects.prefetch_related(
            "images", "tags", "specs", "reviews"
        ).get(id=kwargs["pk"])

        data = format_instance_to_dict(product)  # see utils.py

        if not DEBUG:
            cache.set(cache_key, data, 3600)

    return JsonResponse(data, status=200)


@apply_exception_handler
def write_review_view(request: HttpRequest, **kwargs) -> JsonResponse:
    """
    Publish review about product, if user is authenticated.
    :param request: HttpRequest
    :param kwargs: <pk> of product from urlpattern
    :return: JsonResponse
    """
    def get_reviews(prod: Product) -> list:

        reviews = prod.reviews.all()
        reviews_list = []

        if reviews:
            rate_sum = 0

            for item in reviews:
                data = {
                    "author": get_user_fullname(item.user),
                    "email": item.user.email,
                    "text": item.text,
                    "rate": item.rate,
                    "date": item.created_at.strftime("%Y %B %d, %H:%M, %Z"),
                }
                reviews_list.append(data)

                rate_sum += item.rate

            prod.rating = rate_sum / reviews.count()
            prod.save()

        return reviews_list

    product = get_object_or_404(Product, pk=kwargs["pk"])

    if request.user.is_authenticated:

        data = json.loads(request.body)

        review = ProductReview(
            product=product,
            user=request.user,
            text=data.get("text"),
            rate=data.get("rate"),
        )
        review.full_clean()  # this is validation;
        # if to use <create> - validation is not run.
        review.save()

        return JsonResponse(get_reviews(product), safe=False, status=201)

    else:
        return JsonResponse(get_reviews(product), safe=False, status=400)

