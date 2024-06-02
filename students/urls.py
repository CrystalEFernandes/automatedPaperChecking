from django.contrib import admin
from django.urls import path,include
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', Login, name='login'),
    path('register/', Register, name='register'),
    path('logout/', student_logout, name='student_logout'),
    path('forget-password/', ForgetPassword, name='forget_password'),
    path('change-password/<str:token>/', ChangePassword, name='change_password'),
    path('dashboard/', student_dashboard, name='student_dashboard'),
    path('assignment_download/<path:file_path>', assignment_download, name='assignment_download'),
    path('submit_assignment/<int:assignment_id>/', submit_assignment, name='submit_assignment'),
    path('view-submission/<int:assignment_id>/', view_submission, name='view_submission'),
    path('my_gradings/', view_all_student_submissions, name='view_all_student_submissions'),

    
]

