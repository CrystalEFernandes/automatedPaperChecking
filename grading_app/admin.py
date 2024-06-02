from django.contrib import admin
from .models import Assessment

class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('assessment_id', 'teacher_assignment_file', 'student_assignment_submission_file', 'response','grade')
    list_filter = ('teacher_assignment_file', 'student_assignment_submission_file')
    search_fields = ('assessment_id', 'teacher_assignment_file__title', 'student_assignment_submission_file__title')

admin.site.register(Assessment, AssessmentAdmin)
