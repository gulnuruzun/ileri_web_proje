from django.contrib import admin
from django.urls import path
from core import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Ana Sayfa
    path('', views.course_list, name='dashboard'),
    path('courses/', views.course_list, name='course_list'),

    # Öğrenci Paneli
    path('dashboard/', views.ogrenci_paneli, name='ana_sayfa'),

    # Öğretmen Paneli
    path('ogretmen-paneli/', views.teacher_dashboard, name='teacher_dashboard'),
    path('ogretmen/ders-ekle/', views.add_course, name='add_course'),
    path('teacher/course/<str:course_code>/grade/', views.grade_entry, name='grade_entry'),

    # Admin Paneli
    path('yonetim/', views.admin_dashboard, name='admin_dashboard'),

    # Profil & Akademik
    path('profile/', views.profil_sayfasi, name='profile'),
    path('transcript/', views.transcript_view, name='transcript'),
    path('my-courses/', views.my_courses_view, name='my_courses'),

    # Giriş/Çıkış
    path('login/', views.giris_yap, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Ders
    path('course/<str:course_code>/', views.course_detail, name='course_detail'),
    path('enroll/<str:course_code>/', views.kayit_ol, name='enroll_course'),
]