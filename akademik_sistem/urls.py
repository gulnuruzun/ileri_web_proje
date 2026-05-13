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
    # Views içindeki fonksiyon adının 'teacher_dashboard_view' olduğunu varsayıyorum
    # 'teacher_dashboard_view' yerine 'teacher_dashboard' yazıyoruz
path('ogretmen-paneli/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/course/<str:course_code>/grade/', views.grade_entry, name='grade_entry'),
    # Profil
    path('profile/', views.profil_sayfasi, name='profile'),
    path('transcript/', views.ogrenci_paneli, name='transcript'),  
    path('my-courses/', views.ogrenci_paneli, name='my_courses'),  
    # Giriş/Çıkış
    path('login/', views.giris_yap, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('course/<str:course_code>/', views.course_detail, name='course_detail'),
    path('enroll/<str:course_code>/', views.kayit_ol, name='enroll_course'),
    path('derse-atama/<int:course_id>/', views.derse_atama_yap, name='derse_atama_yap'),
]
