# In your project's urls.py
from django.urls import path
from grading_app import views

urlpatterns = [
    path('activate_grading_app_ungraded/<int:assignment_id>/', views.activate_grading_app_ungraded, name='activate_grading_app_ungraded'),
]
