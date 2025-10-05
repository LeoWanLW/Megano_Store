
from django.contrib import admin

from .models import (Category, CategoryImage, Sale,
                     Product, ProductImage, ProductReview, ProductSpec, ProductTag)


class CategoryImageInline(admin.TabularInline):
    model = CategoryImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ("id", "title", "parent",)
    list_display_links = ("title",)
    search_fields = ("title",)
    readonly_fields = ("id",)
    ordering = ("id",)

    fieldsets = [
        (None, {
            "fields": ("id", "title", "parent",),
        }),
    ]

    inlines = [CategoryImageInline,]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductSpecInline(admin.TabularInline):
    model = ProductSpec
    extra = 1


class ProductTagInline(admin.TabularInline):
    model = ProductTag.product.through
    extra = 1


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    can_add = False
    can_change = False
    can_delete = False
    readonly_fields = [field.name for field in model._meta.fields]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = ("id", "category", "title", "price", "count",
                    "rating", "available",)
    list_display_links = ("title",)
    search_fields = ("category__title", "title",)
    readonly_fields = ("id", "created_at", "created_by",)
    ordering = ("id",)

    fieldsets = [
        (None, {
            "fields": ("category", "title", "description_short", "description_full",),
        }),
        ("Relevancy", {
            "fields": ("price", "count", "available", "free_delivery",),
            "classes": ("collapse", "wide",),
            # "description": ("",),
        }),
        ("Extra options", {
            "fields": ("limited_edition", "created_at", "created_by",),
            "classes": ("collapse", "wide",),
        }),
    ]

    inlines = [
        ProductImageInline,
        ProductSpecInline,
        ProductTagInline,
        ProductReviewInline,
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            kwargs["queryset"] = Category.objects.exclude(parent__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):

    list_display = ("id", "product", "price_sale", "date_from", "date_to",)
    list_display_links = ("product",)
    search_fields = ("product",)
    readonly_fields = ("id",)
    ordering = ("id",)

    fieldsets = [
        (None, {
            "fields": ("id", "product", "price_sale", "date_from", "date_to",),
        }),
    ]

