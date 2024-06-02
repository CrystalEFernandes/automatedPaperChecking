from django.urls import path
from .views import teacher_login, teacher_forgot_password, teacher_change_password, logout_view, teacher_dashboard,view_submissions,teacher_upload,submission_download,view_teacher_assignments,view_student_submissions,download_submission,view_all_assessments,view_grades
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', teacher_login, name='teacher_login'),
    path('forgot_password/', teacher_forgot_password, name='teacher_forgot_password'),
    path('change_password/<str:token>/', teacher_change_password, name='teacher_change_password'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('upload/', teacher_upload, name='teacher_upload'),
    path('submission_download/<path:file_path>', submission_download, name='submission_download'),
    path('view_submissions/<int:student_id>/', view_submissions, name='view_submissions'),
    path('assignments/', view_teacher_assignments, name='view_teacher_assignments'),
    path('assignments/<int:assignment_id>/', view_student_submissions, name='view_student_submissions'),
    path('student_submissions/<str:username>/<int:submission_id>/<str:filename>', download_submission, name='download_submission'),
    path('assessments/', view_all_assessments, name='view_all_assessments'),
    path('view_grades/', view_grades, name='view_grades'),
]
