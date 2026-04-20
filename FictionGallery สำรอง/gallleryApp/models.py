from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.

# Profile Table (แทนที่ User เดิม)
class Profile(models.Model):
    ROLE_CHOICES = (('reader', 'Reader'),('writer', 'Writer'),)

    # เชื่อมโยงกับ Django's built-in User
    user = models.ForeignKey(User,
                             on_delete=models.SET_NULL,   # ถ้า User ถูกลบ จะไม่ลบ Profile แต่ set เป็น NULL
                             null=True,                   # อนุญาตให้ user = None
                             blank=True,                  # อนุญาตให้ฟอร์มเว้นว่าง
                             related_name="profiles")

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="reader")
    pen_name = models.CharField(max_length=120,default="", blank=True)  # นามปากกา
    pen_name_original = models.TextField(blank=True)  # ที่มาของนามปากกา (ไม่บังคับ)
    profile_pic = models.ImageField(upload_to="profile_pic", blank=True)  # รูปโปรไฟล์
    profile_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pen_name} - {self.role}"  # ใช้นามปากกาเป็นตัวแทน



#Status (จะให้สถานะปรับเปลี่ยน/แก้ไขได้บ่อย ๆ)
class Status(models.Model):
    status_id = models.AutoField(primary_key=True)
    status_name = models.CharField(max_length=200,unique=True)
    color = models.CharField(max_length=20,default="#000000")
    description = models.TextField(blank=True)                       # คำอธิบายสถานะ
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.status_name


# Novels Table
class Novels(models.Model):
    novel_id = models.AutoField(primary_key=True)                                              #รหัสนิยาย
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name="novels")    #รหัสuser

    pen_name = models.CharField(max_length=120, blank=True, null=True)                         # นามปากกาเฉพาะเรื่อง
    novel_name = models.CharField(max_length=200)                                              #ชื่อนิยาย
    novel_link = models.URLField()                                                             #linkของนิยาย
    description = models.TextField(blank=True)                                                 #คำอธิบายนิยาย/คำโปรย
    cover_image = models.ImageField(upload_to="cover_image",blank=True, null=True)             #ปกนิยาย
    created_at = models.DateTimeField(default=timezone.now)                                    #วันที่กรอกข้อมูล
    updated_at = models.DateTimeField(auto_now=True)                                           #วันที่อัปเดตข้อมูล

    genres = models.ManyToManyField('Genres', blank=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        # ใช้ pen_name ของเรื่อง ถ้าไม่ได้ใส่ → fallback ไป Profile.pan_name → fallback ไป username
        display_name = (
            self.pen_name if self.pen_name
            else (self.user.profile.pen_name if hasattr(self.user, 'profile') else self.user.username)
        )
        return f"{self.novel_name} by {display_name} - {self.status.status_name if self.status else 'Unknown Status'}"


# Genres Table แนวนิยาย
class Genres(models.Model):
    genre_id = models.AutoField(primary_key=True)                #รหัสแนวนิยาย
    genre_name = models.CharField(max_length=200, unique=True)   #ชื่อแนวนิยาย
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.genre_name


#Reviews(รีวิว/คอมเมนต์)
class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    novel = models.ForeignKey("Novels", on_delete=models.CASCADE,related_name="review")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_by_user")
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.novel.novel_name} - {self.user.username} ({self.rating} ดาว)"

