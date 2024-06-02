from django.db import models
from django.contrib.auth.models import User

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    forget_password_token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    birth_date = models.DateField()
    email = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Teacher)"

def user_directory_path(instance, filename):
    return f'test_assignments/{instance.teacher.user.username}/{instance.assignment_id}/{filename}'

def qfile_path(instance, filename):
    return f'test_assignments/{instance.teacher.user.username}/{instance.assignment_id}/qp/{filename}'

class TestAssignment(models.Model):
    assignment_id = models.AutoField(primary_key=True)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='assigned_tests')
    title = models.CharField(max_length=100)
    description = models.TextField()
    qfile=models.FileField(upload_to=qfile_path)
    file = models.FileField(upload_to=user_directory_path)
    deadline = models.DateTimeField()

    def __str__(self):
        return self.title