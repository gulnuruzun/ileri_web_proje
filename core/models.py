from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (('admin', 'Admin'), ('teacher', 'Teacher'), ('student', 'Student'))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')

class Department(models.Model):
    name = models.CharField(max_length=100)
    building = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_no = models.CharField(max_length=20)
    office_hour = models.CharField(max_length=100, null=True, blank=True)
    assigned_departments = models.ManyToManyField(Department, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    enrollment_date = models.DateField(auto_now_add=True, null=True, blank=True)
    current_gpa = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.student_id} - {self.user.first_name} {self.user.last_name}"

class Course(models.Model):
    code = models.CharField(max_length=10)
    title = models.CharField(max_length=100)
    capacity = models.IntegerField()
    instructor = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    ects_credit = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def is_full(self):
        count = getattr(self, 'enrolled_count', None)
        if count is None:
            count = self.enrollment_set.count()
        return count >= self.capacity

    def __str__(self):
        return f"{self.code} - {self.title}"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    midterm_grade = models.FloatField(null=True, blank=True)
    final_grade = models.FloatField(null=True, blank=True)
    average = models.FloatField(null=True, blank=True)
    letter_grade = models.CharField(max_length=2, null=True, blank=True)
    grade_point = models.FloatField(null=True, blank=True)
    attendance_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.student} - {self.course}"