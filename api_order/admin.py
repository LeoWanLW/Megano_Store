
from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "created_at",)
    list_display_links = ("id", "user",)
    search_fields = ("user__username",)
    readonly_fields = ("id", "created_at",)
    ordering = ("id",)

    fieldsets = [
        (None, {
            "fields": ("id", "user",),
        }),
    ]

    inlines = [CartItemInline,]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "status", "created_at",)
    list_display_links = ("id", "user",)
    search_fields = ("delivery_city", "delivery_address",)
    readonly_fields = ("id", "created_at", "session_key",)
    ordering = ("id",)

    fieldsets = [
        (None, {
            "fields": ("user", "status",),
        }),
        ("Delivery options", {
            "fields": ("delivery_city", "delivery_address", "delivery_type",),
            "classes": ("collapse", "wide",),
            # "description": ("",),
        }),
        ("Payment options", {
            "fields": ("payment_type", "payment_total_cost",),
            "classes": ("collapse", "wide",),
        }),
        ("Extra options", {
            "fields": ("session_key",),
            "classes": ("collapse", "wide",),
        }),
    ]

    inlines = [OrderItemInline,]

