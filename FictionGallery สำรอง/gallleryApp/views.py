from django.shortcuts import render, get_object_or_404 ,redirect
from gallleryApp.models import Genres,Novels,Review,Status,Profile
from django.contrib.auth import authenticate, login as auth_login ,logout as auth_logout
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# Create your views here.
User = get_user_model()

def search(request):
    query = request.GET.get('q', '')

    profiles = []
    novels = []
    reviews = []

    if query:
        # 🔎 ค้นหาใน Profile (นักเขียน)
        profiles = Profile.objects.filter(
            Q(pen_name__icontains=query) |
            Q(pen_name_original__icontains=query) |
            Q(user__username__icontains=query)
        )

        # 🔎 ค้นหาใน Novels (นิยาย)
        novels = Novels.objects.filter(
            Q(novel_name__icontains=query) |
            Q(pen_name__icontains=query) |
            Q(description__icontains=query)
        )

        # 🔎 ค้นหาใน Review (รีวิว)
        reviews = Review.objects.filter(
            Q(comment__icontains=query) |
            Q(novel__novel_name__icontains=query) |   # novel (FK) → novel_name
            Q(user__username__icontains=query)        # user (FK) → username
        )

    context = {
        "query": query,
        "profiles": profiles,
        "novels": novels,
        "reviews": reviews,
    }

    # ✅ เลือก template ตาม role
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return render(request, "search_results_writer.html", context)

        profile = Profile.objects.filter(user=request.user).first()
        if profile and profile.role == "writer":
            return render(request, "search_results_writer.html", context)

    # default → reader
    return render(request, "search_results.html", context)

#-------------------------- ส่วนของreader -----------------------------------
def home(request):
    return render(request, 'home.html')

def biography(request):
    writers = Profile.objects.filter(role="writer")  # ดึงนักเขียนทั้งหมด
    context = {'writers': writers}
    return render(request, 'biography.html', context)

def fiction(request):
    novels = Novels.objects.all()
    return render(request, "fiction.html", {"novels": novels})



#--------------------------- ส่วนของwriter --------------------------------

#สำหรับwriter หน้าเหมือนของ reader ทุกอย่างยกเว้น navbar
def writer_dashboard(request):
    return render(request, 'homeforwriter.html')
#@writer_or_admin_required
def biography_for_writer(request):
    writers = Profile.objects.filter(role="writer")  # ดึงนักเขียนทั้งหมด
    context = {'writers': writers}
    return render(request, 'biographyforwriter.html', context)
#@writer_or_admin_required
def fiction_for_writer(request):
    novels = Novels.objects.all()
    return render(request, 'fictionforwriter.html', {"novels": novels})


#----------------------------------------------------------
#fiction list + create + edid + delete
#@writer_or_admin_required
def fiction_list(request):
    novels = Novels.objects.select_related("user", "status").order_by("-created_at")
    user = request.user
    filter_option = request.GET.get("filter", "")

    # ✅ ถ้าเลือก "ของฉัน" → แสดงนิยายทั้งหมดที่ user ปัจจุบันเป็นเจ้าของ
    if filter_option == "mine" and user.is_authenticated:
        novels = novels.filter(user=user)

    # ✅ ถ้าเลือก pen_name ตาม id ของ Profile
    elif filter_option.isdigit():
        try:
            writer_profile = Profile.objects.get(id=int(filter_option))
            novels = novels.filter(pen_name=writer_profile.pen_name)  # ✅ กรองจากชื่อปากกา
        except Profile.DoesNotExist:
            novels = Novels.objects.none()

    # ✅ กำหนด dropdown ให้ไม่รวม user ตัวเอง (เฉพาะ pen_name คนอื่น)
    if user.is_authenticated:
        writers = Profile.objects.filter(role="writer").exclude(user=user)
    else:
        writers = Profile.objects.filter(role="writer")

    # ✅ pagination
    paginator = Paginator(novels, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "fiction_list.html", {
        "page_obj": page_obj,
        "writers": writers,
    })

#  Create_Novel
def novel_create(request):
    if request.method == "POST":
        # ✅ ดึงค่าฟิลเตอร์เดิมจาก POST หรือ GET
        filter_param = request.POST.get("filter") or request.GET.get("filter") or ""

        status_id = request.POST.get("status")
        status_obj = None
        if status_id and status_id.isdigit():
            try:
                status_obj = Status.objects.get(pk=int(status_id))
            except Status.DoesNotExist:
                status_obj = None

        novel = Novels.objects.create(
            user=request.user,
            pen_name=request.POST.get("pen_name"),
            novel_name=request.POST.get("novel_name"),
            novel_link=request.POST.get("novel_link"),
            description=request.POST.get("description"),
            status=status_obj,
        )

        if "cover_image" in request.FILES:
            novel.cover_image = request.FILES["cover_image"]
            novel.save()

        genres_ids = [gid for gid in request.POST.getlist("genres") if gid.strip()]
        if genres_ids:
            novel.genres.set(genres_ids)

        messages.success(request, "เพิ่มนิยายใหม่เรียบร้อยแล้ว ✅")

        # ✅ แนบ filter เดิมกลับตอน redirect
        redirect_url = reverse("fiction_list")
        if filter_param:
            redirect_url += f"?filter={filter_param}"
        return redirect(redirect_url)

    # ✅ เก็บค่าฟิลเตอร์ไว้ตอน GET เช่น ไปยังฟอร์ม
    filter_param = request.GET.get("filter", "")

    statuses = Status.objects.all()
    genres = Genres.objects.all()
    my_pen_names = Profile.objects.filter(user=request.user).order_by("pen_name")

    return render(
        request,
        "form_fiction.html",
        {
            "statuses": statuses,
            "genres": genres,
            "my_pen_names": my_pen_names,
            "title": "เพิ่มนิยาย",
            "novel": None,
            "filter": filter_param,  # ✅ ส่งไป template ด้วย
        },
    )

# Novel_Edit
@login_required
def novel_edit(request, pk):
    novel = get_object_or_404(Novels, pk=pk)

    # ตรวจสอบสิทธิ์: ต้องเป็นเจ้าของนิยายหรือ Admin เท่านั้น
    if not (request.user == novel.user or request.user.is_superuser):
        messages.error(request, "คุณไม่มีสิทธิ์แก้ไขนิยายนี้ ❌")
        return redirect("fiction_list")

    if request.method == "POST":
        novel.pen_name = request.POST.get("pen_name")
        novel.novel_name = request.POST.get("novel_name")
        novel.novel_link = request.POST.get("novel_link")
        novel.description = request.POST.get("description")

        status_id = request.POST.get("status")
        if status_id:
            novel.status = Status.objects.get(pk=status_id)

        if "cover_image" in request.FILES:
            novel.cover_image = request.FILES["cover_image"]

        novel.save()

        genres_ids = request.POST.getlist("genres")
        if genres_ids:
            novel.genres.set(genres_ids)

        messages.success(request, "แก้ไขนิยายเรียบร้อยแล้ว ✅")
        return redirect("fiction_list")

    statuses = Status.objects.all()
    genres = Genres.objects.all()
    return render(
        request,
        "novel_edit.html",
        {"novel": novel, "statuses": statuses, "genres": genres},
    )

# Novel_Delete
@login_required
def novel_delete(request, pk):
    novel = get_object_or_404(Novels, pk=pk)

    # ตรวจสอบสิทธิ์: ต้องเป็นเจ้าของนิยายหรือ Admin เท่านั้น
    if not (request.user == novel.user or request.user.is_superuser):
        messages.error(request, "คุณไม่มีสิทธิ์ลบนิยายนี้ ❌")
        return redirect("fiction_list")

    if request.method == "POST":
        novel.delete()
        messages.success(request, "ลบนิยายเรียบร้อยแล้ว 🗑️")
        return redirect("fiction_list")

    return render(request, "novel_confirm_delete.html", {"novel": novel})


#-----------------------Writers list + create + edid + delete--------------------------------

def writer_list(request):
    filter_value = request.GET.get("filter")

    # ✅ เริ่ม queryset และกรองแค่ role=writer ก่อนเลย
    writers_qs = Profile.objects.filter(role="writer").order_by("-created_at")

    if filter_value == "mine":
        # ✅ กรณีเลือก "ของฉัน" → ดูเฉพาะ writer ที่เป็นของ user นี้
        writers_qs = writers_qs.filter(user=request.user)
        dropdown_writers = Profile.objects.filter(role="writer").exclude(user=request.user).order_by("pen_name")

    elif filter_value and filter_value.isdigit():
        # ✅ กรณีเลือก penname (id)
        writers_qs = writers_qs.filter(id=filter_value)
        dropdown_writers = Profile.objects.filter(role="writer").exclude(user=request.user).order_by("pen_name")

    else:
        # ✅ กรณี "ทั้งหมด"
        dropdown_writers = Profile.objects.filter(role="writer").order_by("pen_name")

    # ✅ pagination
    paginator = Paginator(writers_qs, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "writers": page_obj,              # สำหรับตาราง
        "page_obj": page_obj,
        "all_writers": dropdown_writers,  # สำหรับ dropdown
    }
    return render(request, "writer_list.html", context)

# Writer_Create
def writer_create(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        selected_filter = request.POST.get("filter", "")  # ✅ ดึงค่าตัวกรอง

        if user_id:
            user = get_object_or_404(User, pk=user_id)
        elif request.user.is_staff:
            user = None
        else:
            user = request.user

        profile = Profile.objects.create(
            user=user,
            pen_name=request.POST.get("pen_name"),
            pen_name_original=request.POST.get("pen_name_original"),
            profile_link=request.POST.get("profile_link"),
            role="writer",
        )

        if "profile_pic" in request.FILES:
            profile.profile_pic = request.FILES["profile_pic"]
            profile.save()

        messages.success(request, f"สร้างโปรไฟล์นักเขียนใหม่ ({profile.pen_name}) สำเร็จ ✨")

        # ✅ ส่งค่าตัวกรองกลับไปหน้า writer_list
        redirect_url = reverse("writer_list")
        if selected_filter:
            redirect_url += f"?filter={selected_filter}"

        return redirect(redirect_url)

    selected_filter = request.GET.get("filter", "")  # ✅ อ่านค่าจาก URL
    users = User.objects.filter(is_staff=False, is_superuser=False)

    return render(request, "writer_create.html", {
        "users": users,
        "filter": selected_filter,  # ✅ ส่งไป template
    })

# Writer_Edit
@login_required
def writer_edit(request, pk):
    writer = get_object_or_404(Profile, pk=pk)

    # ตรวจสอบสิทธิ์: เฉพาะเจ้าของหรือ Admin เท่านั้นที่แก้ไขได้
    if not (request.user == writer.user or request.user.is_staff):
        messages.error(request, "คุณไม่มีสิทธิ์แก้ไขโปรไฟล์นักเขียนนี้ ⚠️")
        return redirect("writer_list")

    if request.method == "POST":
        writer.pen_name = request.POST.get("pen_name")
        writer.pen_name_original = request.POST.get("pen_name_original")
        writer.profile_link = request.POST.get("profile_link")

        if "profile_pic" in request.FILES:
            writer.profile_pic = request.FILES["profile_pic"]

        writer.save()
        messages.success(request, f"แก้ไขข้อมูลนักเขียน ({writer.pen_name}) สำเร็จ ✅")
        return redirect("writer_list")

    return render(request, "writer_edit.html", {"writer": writer})

# Writer_Delete
@login_required
def writer_delete(request, pk):
    writer = get_object_or_404(Profile, pk=pk)

    # ตรวจสอบสิทธิ์: เฉพาะเจ้าของหรือ Admin เท่านั้นที่ลบได้
    if not (request.user == writer.user or request.user.is_staff):
        messages.error(request, "คุณไม่มีสิทธิ์ลบโปรไฟล์นักเขียนนี้ ⚠️")
        return redirect("writer_list")

    if request.method == "POST":
        writer.delete()
        messages.success(request, "ลบนักเขียนเรียบร้อยแล้ว 🗑️")
        return redirect("writer_list")

    return render(request, "writer_confirm_delete.html", {"writer": writer})




#----------------------- Reviews - Reader -----------------------------------------
# แสดงรีวิวทั้งหมด
def review_list(request):
    reviews = Review.objects.select_related("novel", "user").order_by("-created_at")

    # ✅ ตรวจสอบบทบาทสำหรับ staff/admin
    if request.user.is_superuser or request.user.is_staff:
        return render(request, "review_for_writer.html", {"reviews": reviews})

    # ✅ ตรวจสอบก่อนว่า user ล็อกอินแล้วหรือยัง
    if request.user.is_authenticated:
        profiles = request.user.profiles.all()
        if profiles.exists() and profiles.first().role == "writer":
            return render(request, "review_for_writer.html", {"reviews": reviews})

    # ✅ ถ้าไม่ล็อกอิน หรือไม่มี profile → ใช้ template reader ปกติ
    return render(request, "review.html", {"reviews": reviews})


# เพิ่มรีวิว
@login_required
def review_add(request):
    novels = Novels.objects.all()

    if request.method == "POST":
        novel_id = request.POST.get("novel")
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        if not novel_id or not rating or not comment:
            messages.error(request, "กรุณากรอกข้อมูลให้ครบถ้วน")
            return redirect("review_add")

        novel = Novels.objects.get(novel_id=novel_id)
        Review.objects.create(
            novel=novel,
            user=request.user,
            rating=rating,
            comment=comment
        )
        messages.success(request, "เพิ่มรีวิวสำเร็จแล้ว ✅")
        return redirect("review_list")

    # ✅ ตรวจสอบ role เพื่อเลือก template
    profiles = request.user.profiles.all()
    if request.user.is_superuser or request.user.is_staff:
        return render(request, "review_add_for_writer.html", {"novels": novels})
    if profiles.exists() and profiles.first().role == "writer":
        return render(request, "review_add_for_writer.html", {"novels": novels})

    return render(request, "review_add.html", {"novels": novels})

# แก้ไขรีวิว
@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, review_id=review_id, user=request.user)

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        if rating:
            review.rating = int(rating)
        if comment:
            review.comment = comment

        review.save()
        messages.success(request, "แก้ไขรีวิวเรียบร้อยแล้ว ✨")

        # ✅ ตรวจ role
        if request.user.is_superuser or request.user.profiles.filter(role="writer").exists():
            return redirect("review_list_writer")
        else:
            return redirect("review_list")

    novels = Novels.objects.all()
    context = {
        "review": review,
        "novels": novels,
    }

    # ✅ เลือก Template
    if request.user.is_superuser or request.user.profiles.filter(role="writer").exists():
        return render(request, "review_edit_for_writer.html", context)
    else:
        return render(request, "review_edit.html", context)

# ลบรีวิว
@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, review_id=review_id)

    # ✅ สิทธิ์: เจ้าของ หรือ แอดมิน
    if review.user != request.user and not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "คุณไม่มีสิทธิ์ลบรีวิวนี้ ⚠️")
        return redirect("review_list")

    if request.method == "POST":
        review.delete()
        messages.success(request, "ลบรีวิวเรียบร้อยแล้ว 🗑️")
        return redirect("review_list")

    # ✅ เลือก template ตาม role
    profiles = request.user.profiles.all()
    if request.user.is_superuser or request.user.is_staff:
        return render(request, "review_delete_for_writer.html",
                      {"review": review})

    if profiles.exists() and profiles.first().role == "writer":
        return render(request, "review_delete_for_writer.html",
                      {"review": review})

    return render(request, "review_delete.html", {"review": review})

#-------------------- Reviews - Writer ---------------------------------

def review_list_writer(request):
    reviews = Review.objects.select_related("novel", "user").order_by("-created_at")
    context = {
        "reviews": reviews,
    }
    return render(request, "review_for_writer.html", context)


def add_review_writer(request):
    novels = Novels.objects.all()  # โหลดนิยายทั้งหมด

    if request.method == "POST":
        novel_id = request.POST.get("novel")
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        if not novel_id or not rating or not comment:
            messages.error(request, "กรุณากรอกข้อมูลให้ครบถ้วน")
            return redirect("add_review_writer")

        # ✅ ใช้ novel_id แทน id
        novel = Novels.objects.get(novel_id=novel_id)
        Review.objects.create(
            novel=novel,
            user=request.user,
            rating=rating,
            comment=comment
        )
        messages.success(request, "เพิ่มรีวิวสำเร็จแล้ว ✅")
        return redirect("review_list_writer")

    return render(request, "review_add_for_writer.html", {"novels": novels})

#@login_required
def edit_review_writer(request, review_id):
    #ค้นหารีวิวโดยใช้ review_id และตรวจสอบว่าเป็นของ user ที่ login อยู่
    #ถ้าไม่ใช่ หรือหารีวิวไม่เจอ จะคืนค่า 404 (Not Found)
    review = get_object_or_404(Review, review_id=review_id, user=request.user)

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")

        if rating:
            review.rating = int(rating)
        if comment:
            review.comment = comment

        review.save()
        messages.success(request, "แก้ไขรีวิวเรียบร้อยแล้ว ✨")
        return redirect("review_list_writer")

    novels = Novels.objects.all()
    context = {
        "review": review,
        "novels": novels,
    }
    return render(request, "review_edit_for_writer.html", context)

def delete_review_writer(request, review_id):
    # ค้นหารีวิว
    review = get_object_or_404(Review, id=review_id, user=request.user)

    # ตรวจสอบสิทธิ์: ผู้ใช้ที่ login ต้องเป็นเจ้าของรีวิว หรือเป็น Superuser (Admin)
    if request.user == review.user or request.user.is_superuser:
        if request.method == "POST":
            review.delete()
            messages.success(request, "ลบรีวิวเรียบร้อยแล้ว 🗑️")
            return redirect("review_list_writer")
        else:
            return render(request, "review_delete_for_writer.html", {"review": review})
    else:
        #หากไม่มีสิทธิ์ ให้แสดงข้อความแจ้งเตือนและ redirect กลับ
        messages.error(request, "คุณไม่มีสิทธิ์ลบรีวิวนี้ ⚠️")
        return redirect("review_list_writer")


#----------------------- login - logout ----------------------#

def user_login(request):
    if request.user.is_authenticated:
        # ถ้าเป็น superuser ให้เด้งเข้าหน้า admin/dashboard
        if request.user.is_superuser:
            messages.success(request, f"ยินดีต้อนรับผู้ดูแลระบบ {request.user.username}!")
            return redirect("writer_dashboard")

        # ถ้ามี profile
        if request.user.profiles.exists():
            profile = request.user.profiles.first()
            if profile.role == "writer":
                return redirect("writer_dashboard")
            return redirect("home")

        return redirect("home")  # fallback ถ้าไม่มี profile

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)

            if user.is_superuser:
                messages.success(request, f"ยินดีต้อนรับผู้ดูแลระบบ {user.username}!")
                return redirect("writer_dashboard")

            if user.profiles.exists():
                profile = user.profiles.first()
                messages.success(request, f"ยินดีต้อนรับ {profile.pen_name}!")

                if profile.role == "writer":
                    return redirect("writer_dashboard")
                return redirect("home")

            messages.success(request, f"ยินดีต้อนรับ {user.username}!")
            return redirect("home")

        else:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    return render(request, "login.html")

def logout_user(request):
    auth_logout(request)
    messages.success(request, "ออกจากระบบแล้ว")
    return redirect("home")

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role", "reader")  # ค่า default = reader

        # กัน error ถ้ามี username ซ้ำ
        if User.objects.filter(username=username).exists():
            messages.error(request, "ชื่อผู้ใช้นี้ถูกใช้แล้ว")
            return render(request, "register.html")

        # กัน error ถ้ามี email ซ้ำ
        if User.objects.filter(email=email).exists():
            messages.error(request, "อีเมลนี้ถูกใช้แล้ว")
            return render(request, "register.html")

        # สร้าง user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # สร้าง profile และเก็บไว้ในตัวแปร
        profile = Profile.objects.create(
            user=user,
            role=role
        )

        # ✅ ล็อคอินอัตโนมัติหลังสมัคร
        auth_login(request, user)

        # ✅ redirect ตาม role
        if role == "writer":
            # ส่งต่อไปกรอกฟอร์ม Writer
            return redirect("form_writer", profile_id=profile.id)
        return redirect("home")

    return render(request, "register.html")


def form_writer_view(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)

    if request.method == "POST":
        profile.pen_name = request.POST.get("pen_name", "")
        profile.pen_name_original = request.POST.get("pen_name_original", "")
        profile.profile_link = request.POST.get("profile_link", "")

        if "profile_pic" in request.FILES:
            profile.profile_pic = request.FILES["profile_pic"]

        profile.save()
        return redirect("writer_list")  # หรือหน้าอื่นตามที่คุณต้องการ

    return render(request, "form_writer.html", {"profile": profile})


#------------------------------------------------------------------------------

class MyPasswordResetView(auth_views.PasswordResetView):
    template_name = "reset_password.html"

    def form_valid(self, form):
        messages.success(self.request, "📩 เราได้ส่งลิงก์รีเซ็ตรหัสผ่านไปที่อีเมลของคุณแล้ว")
        return super().form_valid(form)