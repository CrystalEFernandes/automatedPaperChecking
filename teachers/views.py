from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import TeacherProfile,TestAssignment
from students.models import StudentProfile,StudentSubmission
from django.contrib.auth import authenticate, login, logout
from .helpers import send_forget_password_mail
import uuid
from django import forms


def teacher_forgot_password(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username')

            if not User.objects.filter(username=username).first():
                messages.success(request, 'No user found with this username.')
                return redirect('teacher_forgot_password')

            user_obj = User.objects.get(username=username)
            token = str(uuid.uuid4())
            profile_obj = TeacherProfile.objects.get(user=user_obj)
            profile_obj.forget_password_token = token
            profile_obj.save()
            send_forget_password_mail(user_obj.email, token)
            messages.success(request, 'An email has been sent.')
            return redirect('teacher_forgot_password')

    except Exception as e:
        print(e)

    return render(request, 'teacher_forget_password.html')

def teacher_change_password(request, token):
    context = {}

    try:
        profile_obj = TeacherProfile.objects.filter(forget_password_token=token).first()
        context = {'user_id': profile_obj.user.id}

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('reconfirm_password')
            user_id = request.POST.get('user_id')

            if user_id is None:
                messages.error(request, 'No user id found.')
                return redirect(f'teacher_change_password/{token}/')

            if new_password != confirm_password:
                messages.error(request, 'Password does not match!')
                return redirect(f'change_password/{token}/')


            user_obj = User.objects.get(id=user_id)
            user_obj.set_password(new_password)
            user_obj.save()
            return redirect('teacher_login')

    except Exception as e:
        print(e)
        messages.error(request, 'An error occurred.')
    return render(request, 'teacher/teacher_change_password.html', context)

def teacher_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Both Username and Password are required.')
            return redirect('teacher_login')

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Invalid username or password.')
            return redirect('teacher_login')

        login(request, user)
        return redirect('teacher_dashboard') 

    return render(request, 'teacher_login.html')

@login_required
def teacher_dashboard(request):
    try:
        teacher_profile = request.user.teacherprofile
        students = StudentProfile.objects.filter(teacher=teacher_profile)
    except TeacherProfile.DoesNotExist:
        teacher_profile = None
        students = StudentProfile.objects.all()
    return render(request, 'teacher_dashboard.html', {'teacher_profile': teacher_profile, 'students': students})


from grading_app.models import Assessment  # Import the Assessment model

def view_submissions(request, student_id):
    student = StudentProfile.objects.get(pk=student_id)
    
    # Fetch submissions based on the Assessment model
    assessments = Assessment.objects.filter(student_assignment_submission_file__student=student.user)
    
    return render(request, 'view_submissions.html', {'student': student, 'assessments': assessments})


import os
from django.http import FileResponse
from django.conf import settings

def submission_download(request, file_path):
    full_file_path = os.path.join(settings.BASE_DIR, file_path)
    return FileResponse(open(full_file_path, 'rb'))

class TestAssignmentForm(forms.ModelForm):
    class Meta:
        model = TestAssignment
        fields = ['title', 'description', 'qfile', 'file', 'deadline']
       

from django.shortcuts import render, redirect
from .models import TeacherProfile
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect

@login_required
def teacher_upload(request):
    if request.method == 'POST':
        form = TestAssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            test_assignment = form.save(commit=False)
            test_assignment.teacher = request.user.teacherprofile
            test_assignment.save()
            return redirect('teacher_dashboard')
    else:
        form = TestAssignmentForm()
    
    return render(request, 'upload_test_assignment.html', {'form': form})

def view_student_submissions(request, assignment_id):
    assignment = get_object_or_404(TestAssignment, pk=assignment_id)
    submissions = StudentSubmission.objects.filter(test_assignment=assignment)

    return render(request, 'view_student_submissions.html', {'assignment': assignment, 'submissions': submissions})

from django.shortcuts import render
from grading_app.models import Assessment


from django.shortcuts import render
from django.db.models import Q  # Import Q for complex queries

def view_grades(request):
    # Retrieve all assessments
    assessments = Assessment.objects.all()

    # Apply filters if any
    username_filter = request.GET.get('username')
    if username_filter:
        assessments = assessments.filter(student_assignment_submission_file__student__username__icontains=username_filter)

    # Sorting by grade (high to low)
    sort_by_grade = request.GET.get('sort_grade')
    if sort_by_grade == 'high_to_low':
        assessments = assessments.order_by('-grade')

    # Sorting by assignment
    sort_by_assignment = request.GET.get('sort_assignment')
    if sort_by_assignment == 'ascending':
        assessments = assessments.order_by('teacher_assignment_file__assignment_id')
    elif sort_by_assignment == 'descending':
        assessments = assessments.order_by('-teacher_assignment_file__assignment_id')

    # Searching by assignment or description
    search_query = request.GET.get('search')
    if search_query:
        assessments = assessments.filter(
            Q(teacher_assignment_file__title__icontains=search_query) | 
            Q(teacher_assignment_file__description__icontains=search_query)
        )

    return render(request, 'view_grades.html', {'assessments': assessments})



def view_teacher_assignments(request):
    teacher = request.user.teacherprofile
    assignments = TestAssignment.objects.filter(teacher=teacher)

    return render(request, 'view_teacher_assignments.html', {'assignments': assignments})

def download_submission(request, file_path):
    full_file_path = os.path.join(settings.BASE_DIR, file_path)
    return FileResponse(open(full_file_path, 'rb'))

def logout_view(request):
    logout(request)
    return redirect('teacher_login')

from django.shortcuts import render
from grading_app.models import Assessment  

def view_all_assessments(request):
    # Retrieve all assessment objects from the database
    assessments = Assessment.objects.all()

    # Process each assessment's response
    for assessment in assessments:
        # Replace ** with <strong> for bold text
        assessment.response = assessment.response.replace('**', '<strong>').replace('**', '</strong>')
        # Replace newlines with HTML line breaks
        assessment.response = assessment.response.replace('\n', '<br>')

    # Render the template with the assessments queryset
    return render(request, 'all_assessments.html', {'assessments': assessments})
