
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

User = get_user_model()


phone_validator = RegexValidator(
    regex=r"^\+?\d{11,13}$",
    message="Enter a correct phone number of 11 to 13 digits. "
        "A plus sign can be at the beginning.",
    code = "invalid_phone_number"
)


def validate_avatar_size(avatar):
    max_size_mb = 2
    if avatar.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File size must not exceed {max_size_mb} MB.")


def user_avatar_path(instance: "Profile", filename: str) -> str:
    return "users/user_{pk}/avatar/{filename}".format(
        pk=instance.belong_to_user.pk,
        filename=filename
    )


class Profile(models.Model):

    belong_to_user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    avatar = models.ImageField(
        validators=[validate_avatar_size],
        max_length=160,
        blank=True,
        default="",
        upload_to=user_avatar_path,
    )
    phone_number = models.CharField(
        validators=[phone_validator],
        max_length=14,
        blank=True,
        default="",
    )

    def __str__(self):
        return "User <" + self.belong_to_user.username + ">"

