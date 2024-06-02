from django.contrib import admin
from .models import StudentProfile, StudentSubmission

class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'birth_date', 'phone', 'created_at', 'teacher')
    search_fields = ('user__username', 'first_name', 'last_name')
    readonly_fields = ('created_at',)

class StudentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'test_assignment', 'file', 'submitted_at', 'submitted', 'graded')
    search_fields = ('student__username', 'test_assignment__title')
    readonly_fields = ('submitted_at',)


admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(StudentSubmission, StudentSubmissionAdmin)
