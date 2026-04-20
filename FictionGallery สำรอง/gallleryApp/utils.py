from django.contrib.auth.models import User, Group
from .models import Profile
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def assign_user_to_group(user, role):
    """
    เพิ่ม user เข้า Group ตาม role
    """
    group, created = Group.objects.get_or_create(name=role.capitalize())
    user.groups.add(group)

def register_user(username, email, password, pen_name, role="reader"):
    """
    สมัครสมาชิก + สร้าง Profile + assign group
    """
    # สร้าง user
    user = User.objects.create_user(username=username, email=email, password=password)

    # สร้าง Profile
    Profile.objects.create(user=user, pen_name=pen_name)

    # assign group
    assign_user_to_group(user, role)

    return user

def writer_or_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "กรุณาเข้าสู่ระบบก่อน ❌")
            return redirect("login")

        if request.user.is_superuser or getattr(request.user, "profile", None) and request.user.profile.role == "writer":
            return view_func(request, *args, **kwargs)

        messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้ ❌")
        return redirect("home")

    return _wrapped_view