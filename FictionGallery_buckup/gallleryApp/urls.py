from gallleryApp import views
from django.contrib.auth import views as auth_views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from gallleryApp.views import novel_create


urlpatterns = [
    path('',views.home,name='home'),
    path('search/', views.search, name='search'),
    path('reader/',views.home,name='reader_home'),

    #ส่วนของreader
    path('biography/',views.biography,name='biography'),
    path('fiction/',views.fiction,name='fiction'),

#review_for_reader
    path("review/", views.review_list, name="review_list"),  # รวมรีวิวทุกนิยาย
    path("reviews/add/", views.review_add, name="review_add"),
    path("reviews/<int:review_id>/edit/", views.edit_review, name="edit_review"),
    path("reviews/<int:review_id>/delete/", views.delete_review, name="delete_review"),


#--------------------------------- Writer - Admin --------------------------------------------

    #ส่วนของสมาชิกเห็น
    path('fiction_list/',views.fiction_list,name='fiction_list'),
    #ส่วนของ เพิ่ม แก้ไข ลบ
    path("novels/create/",novel_create,name="novel_create"),
    path("novel/<int:pk>/edit/", views.novel_edit, name="novel_edit"),  # ✅ เพิ่มตรงนี้
    path("novel/<int:pk>/delete/", views.novel_delete, name="novel_delete"), # Delete


    path('writer_list/',views.writer_list,name='writer_list'),
    #ส่วนของ เพิ่ม แก้ไข ลบ
    path("writers/create/", views.writer_create, name="writer_create"),
    path("writer/<int:pk>/edit/", views.writer_edit, name="writer_edit"),   # ✅ เพิ่มตรงนี้
    path("writers/<int:pk>/delete/", views.writer_delete, name="writer_delete"),



#------------------------------------- Writer - Admin -----------------------------------------
    path('homeforwriter',views.writer_dashboard,name='writer_dashboard'),
    path('biographyforwriter',views.biography_for_writer,name='biographyforwriter'),
    path('fictionforwriter',views.fiction_for_writer,name='fictionforwriter'),

# ✅ Writer & Admin
    path("review_for_writer/", views.review_list_writer, name="review_list_writer"),
    path("reviews/writer/add/", views.add_review_writer, name="add_review_writer"),
    path("reviews/writer/<int:review_id>/edit/", views.edit_review_writer, name="edit_review_writer"),
    path("reviews/writer/<int:review_id>/delete/", views.delete_review_writer, name="delete_review_writer"),




#-------------------------- login - logout  -------------------------------------------------------

    #ส่วนของ login - logout
    path('login/',views.user_login,name='login'),
    path('logout',views.logout_user),
    path('register/', views.register_view, name='register'),
    path('form_writer/<int:profile_id>/', views.form_writer_view,name='form_writer'),


#--------------------------------Reset Password Flow----------------------------------------


    # หน้าให้กรอกอีเมลเพื่อขอ reset
    path("reset_password/",
         auth_views.PasswordResetView.as_view(template_name="reset_password.html"),
         name="reset_password"),

    # แจ้งว่าอีเมลถูกส่งแล้ว
    path("reset_password_sent/",
         auth_views.PasswordResetDoneView.as_view(template_name="reset_password_sent.html"),
         name="password_reset_done"),

    # ลิงก์ที่ส่งไปทางอีเมล (reset form)
    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(template_name="reset_password_confirm.html"),
         name="password_reset_confirm"),

    # แจ้งว่า reset สำเร็จแล้ว
    path("reset_password_complete/",
         auth_views.PasswordResetCompleteView.as_view(template_name="reset_password_complete.html"),
         name="password_reset_complete"),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

