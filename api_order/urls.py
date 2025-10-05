
from django.urls import path, re_path

from . import views

app_name = "api_order"

# 're_path' is applied, because into 'frontend' paths do not have trailing slash,
# which is problem for a 'POST' request.
urlpatterns = [
    re_path(r"^basket/?$", views.get_basket_view, name="basket"),
    re_path(r"^orders/?$", views.get_orders_view, name="orders"),
    path("orders/<int:pk>/", views.get_one_order_view, name="oneorder-with-slash"),
    path("orders/<int:pk>", views.get_one_order_view, name="oneorder-less-slash"),
    path("payment/<int:pk>/", views.order_payment_view, name="payment"),
]

