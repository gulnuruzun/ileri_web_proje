from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.db.models import Count, Q
from .models import Course, Student, Enrollment, Department, Teacher


def _calculate_gpa(enrollments):
    total_points = 0.0
    total_credits = 0
    for e in enrollments:
        if e.grade_point is not None:
            credit = e.course.ects_credit
            total_points += e.grade_point * credit
            total_credits += credit
    if total_credits == 0:
        return 0.0
    return round(total_points / total_credits, 2)


def home(request):
    if request.user.is_authenticated:
        role = str(getattr(request.user, 'role', '')).lower()
        if role == 'teacher' or request.user.username == 'ibrahim':
            return redirect('teacher_dashboard')
        if role == 'admin':
            return redirect('admin_dashboard')
        if role == 'student':
            return redirect('ana_sayfa')
    return course_list(request)


def course_list(request):
    search = request.GET.get('search', '')
    dept_filter = request.GET.get('department', '')

    courses = Course.objects.all().annotate(enrolled_count=Count('enrollment'))
    if search:
        courses = courses.filter(Q(title__icontains=search) | Q(code__icontains=search))
    if dept_filter:
        courses = courses.filter(department_id=dept_filter)
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
        'enrolled_count': course.enrolled_count,
        'is_enrolled': is_enrolled,
    })


@login_required(login_url='login')
def teacher_dashboard(request):
    teacher = Teacher.objects.filter(user=request.user).first()

    if teacher is None:
        return render(request, 'core/accounts/teacher_dashboard.html', {
            'teacher': None,
            'courses': [],
            'total_students': 0,
            'course_count': 0,
            'error': 'Öğretmen profili yok.',
        })

    my_courses = Course.objects.filter(instructor=teacher).annotate(enrolled_count=Count('enrollment'))

    return render(request, 'core/accounts/teacher_dashboard.html', {
        'teacher': teacher,
        'courses': my_courses,
        'total_students': Enrollment.objects.filter(course__in=my_courses).count(),
        'course_count': my_courses.count(),
    })


@login_required(login_url='login')
def teacher_courses(request):
    teacher = Teacher.objects.filter(user=request.user).first()

    if teacher is None:
        return render(request, 'core/courses/teacher_courses.html', {
            'teacher': None,
            'courses': [],
            'error': 'Öğretmen profili yok.',
        })

    courses = Course.objects.filter(instructor=teacher).annotate(enrolled_count=Count('enrollment'))

    return render(request, 'core/courses/teacher_courses.html', {
        'teacher': teacher,
        'courses': courses,
    })


@login_required(login_url='login')
def add_course(request):
    teacher = Teacher.objects.filter(user=request.user).first()
    if teacher is None:
        return redirect('teacher_dashboard')

    departments = Department.objects.all()
    errors = []
    form_data = {}

    if request.method == 'POST':
        form_data = {
            'code': request.POST.get('code', '').strip(),
            'title': request.POST.get('title', '').strip(),
            'capacity': request.POST.get('capacity', '').strip(),
            'ects_credit': request.POST.get('ects_credit', '').strip(),
            'department': request.POST.get('department', '').strip(),
        }

        code = form_data['code']
        title = form_data['title']

        if not code:
            errors.append('Ders kodu gerekli.')
        if not title:
            errors.append('Ders adı gerekli.')
        if code and Course.objects.filter(code=code).exists():
            errors.append('Bu kod ile bir ders zaten var.')

        try:
            capacity_int = int(form_data['capacity'])
            if capacity_int < 1:
                errors.append('Kontenjan en az 1 olmalı.')
        except (ValueError, TypeError):
            capacity_int = None
            errors.append('Kontenjan sayı olmalı.')

        try:
            ects_int = int(form_data['ects_credit']) if form_data['ects_credit'] else 5
        except (ValueError, TypeError):
            ects_int = None
            errors.append('AKTS sayı olmalı.')

        if not errors:
            department = Department.objects.filter(id=form_data['department']).first() if form_data['department'] else None
            Course.objects.create(
                code=code,
                title=title,
                capacity=capacity_int,
                ects_credit=ects_int,
                instructor=teacher,
                department=department,
            )
            return redirect('teacher_dashboard')

    return render(request, 'core/courses/add_course.html', {
        'departments': departments,
        'errors': errors,
        'form_data': form_data,
    })


@login_required(login_url='login')
def grade_entry(request, course_code):
    course = get_object_or_404(Course, code=course_code)

    teacher = Teacher.objects.filter(user=request.user).first()
    if teacher is None or course.instructor_id != teacher.id:
        return redirect('teacher_dashboard')

    enrollments = Enrollment.objects.filter(course=course)

    if request.method == "POST":
        for e in enrollments:
            midterm_raw = request.POST.get(f'midterm_{e.id}')
            final_raw = request.POST.get(f'final_{e.id}')
            attendance_raw = request.POST.get(f'attendance_{e.id}')

            try:
                if midterm_raw and midterm_raw.strip():
                    e.midterm_grade = float(midterm_raw)

                if final_raw and final_raw.strip():
                    e.final_grade = float(final_raw)

                if attendance_raw and attendance_raw.strip():
                    e.attendance_count = int(attendance_raw)

                if e.midterm_grade is not None and e.final_grade is not None:
                    ortalama = (e.midterm_grade * 0.4) + (e.final_grade * 0.6)
                    e.average = ortalama

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

                e.save()

            except (ValueError, TypeError):
                continue

        affected_students = {e.student for e in enrollments}
        for st in affected_students:
            st_enrollments = Enrollment.objects.filter(student=st).select_related('course')
            st.current_gpa = _calculate_gpa(st_enrollments)
            st.save()

        return redirect('teacher_dashboard')

    return render(request, 'core/courses/grade_entry.html', {
        'course': course,
        'enrollments': enrollments
    })


@login_required(login_url='login')
def ogrenci_paneli(request):
    ogrenci = Student.objects.filter(user=request.user).first()

    if ogrenci is None:
        return render(request, 'core/accounts/student_dashboard.html', {
            'student': None,
            'enrollments': [],
            'gpa': 0.0,
            'course_count': 0,
            'total_credits': 0,
            'error': 'Öğrenci profili yok.',
        })

    kayitlar = Enrollment.objects.filter(student=ogrenci).select_related('course', 'course__instructor', 'course__instructor__user')

    kayitli_ders_sayisi = kayitlar.count()
    toplam_ects = sum(kayit.course.ects_credit for kayit in kayitlar)
    gpa = _calculate_gpa(kayitlar)

    return render(request, 'core/accounts/student_dashboard.html', {
        'enrollments': kayitlar,
        'student': ogrenci,
        'gpa': gpa,
        'course_count': kayitli_ders_sayisi,
        'total_credits': toplam_ects,
    })


@login_required(login_url='login')
def transcript_view(request):
    student = Student.objects.filter(user=request.user).first()

    if student is None:
        return render(request, 'core/courses/transcript.html', {
            'student': None,
            'enrollments': [],
            'gpa': 0.0,
            'total_courses': 0,
            'total_ects': 0,
            'passed_count': 0,
            'failed_count': 0,
            'error': 'Öğrenci profili yok.',
        })

    enrollments = Enrollment.objects.filter(student=student).select_related('course')

    gpa = _calculate_gpa(enrollments)
    total_ects = sum(e.course.ects_credit for e in enrollments)
    passed = sum(1 for e in enrollments if e.letter_grade and e.letter_grade not in ('FF', 'FD'))
    failed = sum(1 for e in enrollments if e.letter_grade in ('FF', 'FD'))

    return render(request, 'core/courses/transcript.html', {
        'student': student,
        'enrollments': enrollments,
        'gpa': gpa,
        'total_courses': enrollments.count(),
        'total_ects': total_ects,
        'passed_count': passed,
        'failed_count': failed,
    })


@login_required(login_url='login')
def my_courses_view(request):
    student = Student.objects.filter(user=request.user).first()

    if student is None:
        return render(request, 'core/courses/my_courses.html', {
            'enrollments': [],
            'total_ects': 0,
            'gpa': 0.0,
            'error': 'Öğrenci profili yok.',
        })

    enrollments = Enrollment.objects.filter(student=student).select_related('course', 'course__department')

    total_ects = sum(e.course.ects_credit for e in enrollments)
    gpa = _calculate_gpa(enrollments)

    return render(request, 'core/courses/my_courses.html', {
        'enrollments': enrollments,
        'total_ects': total_ects,
        'gpa': gpa,
    })


@login_required(login_url='login')
def admin_dashboard(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('dashboard')

    students = Student.objects.select_related('user', 'department').all()
    teachers = Teacher.objects.select_related('user').all()
    courses = Course.objects.annotate(enrolled_count=Count('enrollment')).select_related('department', 'instructor', 'instructor__user').all()

    return render(request, 'core/accounts/admin_dashboard.html', {
        'students': students,
        'teachers': teachers,
        'courses': courses,
        'student_count': students.count(),
        'teacher_count': teachers.count(),
        'course_count': courses.count(),
        'department_count': Department.objects.count(),
    })


def giris_yap(request):
    if request.method == "POST":
        u_name = request.POST.get('username')
        p_word = request.POST.get('password')
        user = authenticate(request, username=u_name, password=p_word)

        if user is not None:
            login(request, user)
            if u_name == 'ibrahim' or (hasattr(user, 'role') and str(user.role).lower() == 'teacher'):
                return redirect('teacher_dashboard')
            if hasattr(user, 'role') and str(user.role).lower() == 'admin':
                return redirect('admin_dashboard')
            if hasattr(user, 'role') and str(user.role).lower() == 'student':
                return redirect('ana_sayfa')
            return redirect('dashboard')
        else:
            return render(request, 'core/accounts/login.html', {'error': 'Hatalı giriş!'})

    return render(request, 'core/accounts/login.html')


@login_required(login_url='login')
def kayit_ol(request, course_code):
    course = get_object_or_404(Course.objects.annotate(enrolled_count=Count('enrollment')), code=course_code)
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('dashboard')

    already_enrolled = Enrollment.objects.filter(student=student, course=course).exists()

    if request.method == "POST":
        if already_enrolled:
            return render(request, 'core/courses/enrollment_form.html', {
                'course': course,
                'already_enrolled': True,
                'error': 'Bu derse zaten kayıtlısın.',
            })
        if course.enrolled_count >= course.capacity:
            return render(request, 'core/courses/enrollment_form.html', {
                'course': course,
                'error': 'Bu dersin kontenjanı doldu.',
            })
        Enrollment.objects.create(student=student, course=course)
        return redirect('ana_sayfa')

    return render(request, 'core/courses/enrollment_form.html', {
        'course': course,
        'already_enrolled': already_enrolled,
    })


@login_required(login_url='login')
def profil_sayfasi(request):
    student = None
    teacher = None
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        pass
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        pass

    message = None
    error = None

    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'update_email':
            new_email = request.POST.get('email', '').strip()
            if not new_email:
                error = 'E-posta boş olamaz.'
            elif new_email == request.user.email:
                error = 'Yeni e-posta eskisiyle aynı olamaz.'
            else:
                request.user.email = new_email
                request.user.save()
                message = 'E-posta güncellendi.'

        elif action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not request.user.check_password(current_password):
                error = 'Mevcut şifre hatalı.'
            elif new_password != confirm_password:
                error = 'Yeni şifreler eşleşmiyor.'
            elif len(new_password) < 6:
                error = 'Yeni şifre en az 6 karakter olmalı.'
            elif new_password == current_password:
                error = 'Yeni şifre eskisiyle aynı olamaz.'
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                message = 'Şifre güncellendi.'

    return render(request, 'core/accounts/profile.html', {
        'user': request.user,
        'student': student,
        'teacher': teacher,
        'message': message,
        'error': error,
    })
