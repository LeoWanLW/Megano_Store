
from django.urls import path

from . import views

app_name = "api_product"

# 're_path' is applied, because into 'frontend' paths do not have trailing slash,
# which is problem for a 'POST' request.
urlpatterns = [
    path("categories/", views.get_categories_view, name="categories"),
    path("tags/", views.get_tags_view, name="tags"),
    path("catalog/", views.get_catalog_view, name="catalog"),
    path("banners/", views.get_banners_view, name="banners"),
    path("products/limited/", views.get_limited_view, name="limited"),
    path("products/popular/", views.get_popular_view, name="popular"),
    path("sales/", views.get_sales_view, name="sales"),
    path("product/<int:pk>/", views.get_product_view, name="product"),
    path("product/<int:pk>/reviews", views.write_review_view,
         name="product-review"),
]
