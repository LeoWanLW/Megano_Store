
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Category(models.Model):
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT
    )
    title = models.CharField(max_length=128, db_index=True)

    def __str__(self):
        return self.title


def category_image_path(instance: "CategoryImage", filename: str) -> str:
    return f"categories/category_{instance.pk}/images/{filename}"


class CategoryImage(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(
        blank=True,
        default="",
        upload_to=category_image_path
    )
    description = models.CharField(
        max_length=128,
        blank=True,
        default=""
    )

    def __str__(self):
        return "Image for category " + self.category.title


class Product(models.Model):
    """
    Field <title_low> is added, because when using Cyrillic characters,
    the search is always performed taking into account the case of characters
    in the records of database SQLite.
    """
    class Meta:
        ordering = ["created_at", "category_id"]

    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    title = models.CharField(max_length=192, db_index=True)
    title_low = models.CharField(
        max_length=192,
        default="",
        db_index=True,
        editable=False
    )
    description_short = models.TextField(
        blank=True,
        default="",
        db_index=True
    )
    description_full = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    count = models.PositiveSmallIntegerField(default=0)
    available = models.BooleanField(default=False)
    free_delivery = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    limited_edition = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.title_low = self.title.lower()
        super().save(*args, **kwargs)


def product_image_path(instance: "ProductImage", filename: str) -> str:
    return f"products/product_{instance.pk}/images/{filename}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(
        blank=True,
        default="",
        upload_to=product_image_path
    )
    description = models.CharField(
        max_length=128,
        blank=True,
        default=""
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Image for product " + self.product.title


class ProductSpec(models.Model):
    class Meta:
        default_related_name = "specs"
        ordering = ["parameter"]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    parameter = models.CharField(max_length=64, blank=True, default="")
    value = models.CharField(max_length=256, blank=True, default="")

    def __str__(self):
        return "Specification for product " + self.product.title


class ProductReview(models.Model):
    class Meta:
        default_related_name = "reviews"
        ordering = ["created_at"]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(default="Review")
    rate = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Review for product " + self.product.title


class ProductTag(models.Model):
    product = models.ManyToManyField(Product, related_name="tags")
    value = models.CharField(max_length=32, default="tag")

    def __str__(self):
        return self.value


class Sale(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    price_sale = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    date_from = models.DateField(null=True, blank=True, default=None)
    date_to = models.DateField(null=True, blank=True, default=None)

    def __str__(self):
        return "Sale"

