
from django.contrib.auth import get_user_model
from django.db import models

from api_product.models import Product

User = get_user_model()


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return "Basket for user " + self.user.username
        else:
            return "Basket for anonymous user"


class CartItem(models.Model):
    class Meta:
        default_related_name = "cartitems"
        unique_together = ("cart", "product")

    cart = models.ForeignKey(Cart, related_name="cartitems", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        if self.cart.user:
            return "Basket item for user " + self.cart.user.username
        else:
            return "Basket item for anonymous user"


class Order(models.Model):
    class Meta:
        default_related_name = "orders"
        ordering = ["created_at"]
        get_latest_by = "created_at"

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=48, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=24, null=True, blank=True, default="")
    delivery_type = models.CharField(max_length=32, null=True, blank=True, default="")
    delivery_city = models.CharField(max_length=32, null=True, blank=True, default="")
    delivery_address = models.TextField(null=True, blank=True, default="",
                                        db_index=True)
    payment_type = models.CharField(max_length=32,null=True, blank=True, default="")
    payment_total_cost = models.DecimalField(max_digits=9, decimal_places=2,
                                             null=True, default=0)

    def __str__(self):
        if self.user:
            return f"Order ID {self.id} for user " + self.user.username
        else:
            return (f"Order ID {self.id} for anonymous user (session with key <" +
                    self.session_key + ">)")


class OrderItem(models.Model):
    class Meta:
        default_related_name = "orderitems"
        unique_together = ("order", "product")

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        if self.order.user:
            return (f"Item of order {self.order_id} for user " +
                    self.order.user.username)
        else:
            return (f"Item of order {self.order_id} for anonymous user " +
                    "(session with key <" + self.order.session_key + ">)")

