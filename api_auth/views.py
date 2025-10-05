
import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.http import HttpRequest, JsonResponse

from .models import Profile
from api_order.cart import save_session_cart_to_db
from api_order.models import Order
from megano_store.utils import apply_exception_handler, get_user_fullname, write_errors

User = get_user_model()


def if_session_order_exists(request: HttpRequest, user: User,
                            is_register: bool) -> None:
    """
    Check if there is order linked to the <session_key>.
    If there is - link it to the request user (and clear <session_key>),
    else invoke function <save_session_cart_to_db>.
    Finally, log in the user.
    :param request: HttpReques
    :param user: request user
    :param is_register: if True - register; if False - log in
      (used in function <save_session_cart_to_db>).
    :return: None
    """
    order = Order.objects.filter(session_key=request.session.session_key,
                                 user__isnull=True).first()
    if order:
        order.user = user
        order.session_key = None
        order.save()
    else:
        if is_register:
            save_session_cart_to_db(request, user)
        else:
            save_session_cart_to_db(request)
    login(request, user)


@apply_exception_handler
def user_register_or_login_view(request: HttpRequest) -> JsonResponse:
    """
    Register or log in user. Previously invoke functions:
    - if_session_order_exists;
    - save_session_cart_to_db.
    :param request: HttpRequest
    :return: JsonResponse
    """
    errors = {}
    firstname = ""
    is_register = False

    data = json.loads(request.body)
    username = data.get("username").strip()
    password = data.get("password").strip()

    if "name" in data:
        firstname = data.get("name").strip()
        is_register = True

    if username:
        if password:

            if is_register:

                if User.objects.filter(username=username).exists():
                    errors["UserNameError"]=f"<{username}> user`s name already exists."

                else:
                    validate_password(password)

                    user = User.objects.create_user(username=username,
                                                    password=password,
                                                    first_name=firstname)
                    Profile.objects.create(belong_to_user=user)

                    if_session_order_exists(request,user, True)

                    data = {"userID": user.pk,
                            "message": "User is created and logged in."}

                    return JsonResponse(data, status=201)

            else:
                user = authenticate(username=username, password=password)

                if user and user.is_active:

                    if_session_order_exists(request, user, False)

                    data = {"userID": user.pk, "message": "User is logged in."}

                    return JsonResponse(data, status=200)

                else:
                    errors["AuthError"] = "Authentication error."

        else:
            errors["PasswordError"] = "Password is empty."
    else:
        errors["UserNameError"] = "UserName is empty."

    write_errors(errors, "errors_from_if.log")

    return JsonResponse(errors, status=400)


def user_logout_view(request: HttpRequest) -> JsonResponse:
    """
    Invoke function <save_session_cart_to_db> for save
    session basket to the database and logout user.
    :param request: HttpRequest
    :return: JsonResponse
    """
    save_session_cart_to_db(request)
    logout(request)

    return JsonResponse({"message": "User is logged out."}, status=200)


@apply_exception_handler
def user_profile_view(request: HttpRequest) -> JsonResponse|None:
    """
    Get or update user profile.
    :param request: HttpRequest
    :return: JsonResponse
    """
    def get_user_profile(user: User, profile: Profile) -> dict:

        return {"fullName": get_user_fullname(user),
                "email": user.email,
                "phone": profile.phone_number,
                "avatar": {"src": profile.avatar.url if profile.avatar else "",
                           "alt": profile.belong_to_user.username + "_avatar"}}

    curr_user = request.user
    curr_user_profile = curr_user.profile

    if request.method == "GET":
        return JsonResponse(get_user_profile(curr_user, curr_user_profile), status=200)

    elif request.method == "POST":

        errors = {}
        data = json.loads(request.body)

        full_name = data.get("fullName").split(maxsplit=1)
        curr_user.first_name = full_name[0]
        if len(full_name) > 1:
            curr_user.last_name = full_name[1]

        email = data.get("email").strip()
        if User.objects.filter(email=email).exists():
            errors["UserEmailError"] = f"Email <{email}> already exists."

        phone = data.get("phone").strip()
        if Profile.objects.filter(phone_number=phone).exists():
            errors["UserPhoneError"] = f"Phone number <{phone}> already exists."

        if errors:
            write_errors(errors, "errors_from_if.log")
            return JsonResponse(errors, status=400)

        else:
            curr_user.email = email
            curr_user.save()
            curr_user_profile.phone_number = phone
            curr_user_profile.save()

            updated_data = get_user_profile(curr_user, curr_user_profile)
            return JsonResponse(updated_data, status=200)


@apply_exception_handler
def change_user_password_view(request: HttpRequest) -> JsonResponse:

    curr_user = request.user
    data = json.loads(request.body)

    password_curr = data.get("currentPassword").strip()
    password_new = data.get("newPassword").strip()

    if curr_user.check_password(password_curr):
        validate_password(password_new)
        curr_user.set_password(password_new)
        curr_user.save()

        return JsonResponse({"Success": "Your password has been changed."}, status=200)

    else:
        errors = {"PasswordError": "Current password is not valid."}
        write_errors(errors, "errors_from_if.log")

        return JsonResponse(errors, status=400)


@apply_exception_handler
def upload_user_avatar_view(request: HttpRequest) -> JsonResponse:

    new_avatar = request.FILES.get("avatar")

    if new_avatar:
        profile = request.user.profile
        profile.avatar = new_avatar
        profile.save()
        return JsonResponse({"Success": "New avatar has been set."}, status=201)

    else:
        errors = {"UploadError": "New avatar file has not been uploaded."}
        write_errors(errors, "errors_from_if.log")
        return JsonResponse(errors, status=400)

