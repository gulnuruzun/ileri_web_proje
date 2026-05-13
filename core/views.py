from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from .models import Course, Student, Enrollment, Department, Teacher
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

def course_list(request):
    search = request.GET.get('search', '')
    dept_filter = request.GET.get('department', '')

    courses = Course.objects.all().annotate(enrolled_count=Count('enrollment'))
    if search:
        courses = courses.filter(Q(title__icontains=search) | Q(code__icontains=search))
    if dept_filter:
       # courses = courses.filter(department_id=dept_filter)
       pass
    departments = Department.objects.all()
    return render(request, 'core/courses/course_list.html', {
        'courses': courses,
        'search': search,
        'departments': departments,
        'dept_filter': dept_filter,
    })


def course_detail(request, course_code):
    course = get_object_or_404(Course.objects.annotate(enrolled_count=Count('enrollment')), code=course_code)
    is_enrolled = False
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            is_enrolled = Enrollment.objects.filter(course=course, student=student).exists()
        except Student.DoesNotExist:
            is_enrolled = False

    return render(request, 'core/courses/course_detail.html', {
        'course': course,
        'is_enrolled': is_enrolled,
    })


@login_required(login_url='login')
def teacher_dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return redirect('dashboard')

    my_courses = Course.objects.filter(instructor=teacher).annotate(enrolled_count=Count('enrollment'))
    
    available_courses = Course.objects.filter(instructor__isnull=True).annotate(enrolled_count=Count('enrollment'))
    
    return render(request, 'core/accounts/teacher_dashboard.html', {
        'courses': my_courses,
        'available_courses': available_courses, 
        'total_students': Enrollment.objects.filter(course__in=my_courses).count(),
        'course_count': my_courses.count(),
        'teacher': teacher, 
    })
@login_required(login_url='login')
def grade_entry(request, course_code):
    course = get_object_or_404(Course, code=course_code)
    enrollments = Enrollment.objects.filter(course=course)

    if request.method == "POST":
        for e in enrollments:
            # HTML formundan gelen verileri alıyoruz
            midterm_raw = request.POST.get(f'midterm_{e.id}')
            final_raw = request.POST.get(f'final_{e.id}')
            attendance_raw = request.POST.get(f'attendance_{e.id}')

            try:
                # Verileri sayıya çeviriyoruz (Boşsa veya geçersizse hata almamak için)
                if midterm_raw and midterm_raw.strip():
                    e.midterm_grade = float(midterm_raw)
                
                if final_raw and final_raw.strip():
                    e.final_grade = float(final_raw)
                
                if attendance_raw and attendance_raw.strip():
                    e.attendance_count = int(attendance_raw)

                # OTOMATİK HESAPLAMA (Transkriptin dolması için kritik kısım)
                if e.midterm_grade is not None and e.final_grade is not None:
                    # Ortalama Hesabı (%40 - %60)
                    ortalama = (e.midterm_grade * 0.4) + (e.final_grade * 0.6)
                    
                    # Harf Notu ve Katsayı Belirleme
                    if ortalama >= 90:
                        e.letter_grade = 'AA'
                        e.grade_point = 4.0
                    elif ortalama >= 80:
                        e.letter_grade = 'BA'
                        e.grade_point = 3.5
                    elif ortalama >= 70:
                        e.letter_grade = 'BB'
                        e.grade_point = 3.0
                    elif ortalama >= 60:
                        e.letter_grade = 'CB'
                        e.grade_point = 2.5
                    elif ortalama >= 50:
                        e.letter_grade = 'CC'
                        e.grade_point = 2.0
                    else:
                        e.letter_grade = 'FF'
                        e.grade_point = 0.0
                
                # Değişiklikleri Veritabanına Yaz
                e.save()

            except (ValueError, TypeError):
                # Eğer hoca sayı yerine harf girerse sistem çökmesin diye pas geçiyoruz
                continue
        
        # İşlem bitince öğretmeni geri gönder
        return redirect('teacher_dashboard')

    return render(request, 'core/courses/grade_entry.html', {
        'course': course,
        'enrollments': enrollments
    })
# 1. ANA SAYFA (Ders Listesi)
def ana_sayfa(request, course_code=None):
    if course_code:
        return redirect('enroll_course', course_code=course_code)
    return redirect('dashboard')
# 2. ÖĞRENCİ PANELİ (Dashboard)
@login_required(login_url='login')
def ogrenci_paneli(request):
    try:
        ogrenci = Student.objects.get(user=request.user)
        kayitlar = Enrollment.objects.filter(student=ogrenci)
        
       
        kayitli_ders_sayisi = kayitlar.count()
      
        toplam_akts = sum(kayit.course.akts for kayit in kayitlar)

        return render(request, 'core/accounts/student_dashboard.html', {
            'enrollments': kayitlar,
            'student': ogrenci,  
            'gpa': "3.50",    
            'course_count': kayitli_ders_sayisi, 
            'total_credits': toplam_akts,      
        })
    except Student.DoesNotExist:
        return redirect('ana_sayfa')
# 3. GİRİŞ YAPMA (Login)
@csrf_exempt
def giris_yap(request):
    # HATAYI ÖNLEYEN SATIR: Değişkeni en başta boş olarak tanımlıyoruz
    user = None 

    if request.method == "POST":
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')
        user = authenticate(request, username=u_name, password=p_word)

        if user is not None:
            login(request, user)
            if u_name == 'ibrahim' or (hasattr(user, 'role') and str(user.role).lower() == 'teacher'):
                return redirect('teacher_dashboard')
            return redirect('dashboard')
        else:
            return render(request, 'core/accounts/login.html', {'error': 'Hatalı giriş!'})

    # GET isteğinde (sayfa ilk açıldığında) hata almamak için render burada
    return render(request, 'core/accounts/login.html')
      
@login_required(login_url='login')
def kayit_ol(request, course_code):
    course = get_object_or_404(Course, code=course_code)
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('dashboard')

    if request.method == "POST":
        Enrollment.objects.get_or_create(student=student, course=course)
        return redirect('dashboard')
        
    return render(request, 'core/courses/enrollment_form.html', {'course': course})
# 5. PROFİL SAYFASI
@login_required(login_url='login')
def profil_sayfasi(request):
    return render(request, 'core/accounts/profile.html', {'user': request.user})


def derse_atama_yap(request, course_id):
    course = get_object_or_404(Course, id=course_id)
  
    teacher = Teacher.objects.get(user=request.user)

    course.instructor = teacher
    course.save()
    
    return redirect('teacher_dashboard')
