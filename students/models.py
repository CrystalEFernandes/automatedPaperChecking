from django.db import models
from django.contrib.auth.models import User
from teachers.models import TeacherProfile, TestAssignment

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    birth_date = models.DateField()
    phone = models.CharField(max_length=20)
    forget_password_token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} (Student)"

def submission_directory_path(instance, filename):
    return f'student_submissions/{instance.student.username}/{instance.test_assignment.assignment_id}/{filename}'

def ocr_directory_path(instance, filename):
    return f'student_submissions/{instance.student.username}/{instance.test_assignment.assignment_id}/ocr/{filename}'

class StudentSubmission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_submissions')
    test_assignment = models.ForeignKey(TestAssignment, on_delete=models.CASCADE)
    file = models.FileField(upload_to=submission_directory_path)
    ocr_file = models.FileField(upload_to=ocr_directory_path, blank=True, null=True)  # Field for OCR file path
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted = models.BooleanField(default=False)
    graded = models.BooleanField(default=False,editable=True)


    def __str__(self):
        return f"{self.student.username}'s submission for Assignment ID {self.test_assignment.assignment_id}"