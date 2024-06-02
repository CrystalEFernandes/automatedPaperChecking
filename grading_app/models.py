# In automated_paper_checker/models.py
from django.db import models
from django.contrib.auth.models import User
from teachers.models import TestAssignment
from students.models import StudentSubmission

class Assessment(models.Model):
    assessment_id = models.AutoField(primary_key=True)
    teacher_assignment_file = models.ForeignKey(TestAssignment, on_delete=models.CASCADE, related_name='teacher_assignments')
    student_assignment_submission_file = models.ForeignKey(StudentSubmission, on_delete=models.CASCADE, related_name='student_submissions')
    response = models.TextField()
    grade = models.FloatField(default=0.0)  # New field to store the grade
    
    def __str__(self):
        return f"Assessment {self.assessment_id}"
