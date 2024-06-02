# teachers/admin.py

from django.contrib import admin
from .models import TeacherProfile, TestAssignment

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'forget_password_token', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(TestAssignment)
class TestAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'title', 'description', 'deadline')
    search_fields = ('teacher__username', 'title')
