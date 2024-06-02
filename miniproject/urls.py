from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('' , include('students.urls')),
    path('admin/', admin.site.urls),
    path('teacher/', include('teachers.urls')),
    path('grading/', include('grading_app.urls')),
]