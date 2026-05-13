from django.contrib import admin
from .models import User, Department, Teacher, Student, Course, Enrollment

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
   
    list_display = ('user', 'staff_no')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'user', 'department')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'capacity', 'instructor')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
  
    list_display = ('student', 'course')

admin.site.register(Department)