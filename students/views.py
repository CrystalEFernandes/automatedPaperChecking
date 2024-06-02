from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import StudentProfile, StudentSubmission
from django.contrib.auth import authenticate, login, logout
from .helpers import send_forget_password_mail
from teachers.models import TeacherProfile,TestAssignment
from uuid import uuid4
from django import forms
import os,io
from google.cloud import vision
from google.cloud.vision_v1 import types
import cv2
import os
from PyPDF2 import PdfReader  # Import PdfReader class from PyPDF2
import cv2
import numpy as np
from pdf2image import convert_from_path


os.environ['GOOGLE_APPLICATION_CREDENTIALS']=r'XXXX.json'

client = vision.ImageAnnotatorClient()

# Login view
def Login(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            if not username or not password:
                messages.success(request, 'Both Username and Password are required.')
                return redirect('/login/')

            user = authenticate(username=username, password=password)

            if user is None:
                messages.success(request, 'Invalid username or password.')
                return redirect('/login/')

            login(request, user)
            return redirect('/dashboard')  

    except Exception as e:
        print(e)

    return render(request, 'login.html')

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['first_name', 'last_name', 'birth_date', 'phone', 'teacher']
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(StudentRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['teacher'].queryset = TeacherProfile.objects.all()

def Register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(username=request.POST['username'], password=request.POST['password'])
            student = form.save(commit=False)
            student.user = user
            student.save()

            return redirect('welcome') 
    else:
        form = StudentRegistrationForm()

    return render(request, 'register.html', {'form': form})

def student_logout(request):
    logout(request)
    return redirect('/')

@login_required(login_url='/login/')
def Home(request):
    return render(request, 'home.html')

def ChangePassword(request, token):
    context = {}

    try:
        student_profile_obj = StudentProfile.objects.filter(forget_password_token=token).first()
        context = {'user_id': student_profile_obj.user.id}

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('reconfirm_password')
            user_id = request.POST.get('user_id')

            if user_id is None:
                messages.success(request, 'No user id found.')
                return redirect(f'/change-password/{token}/')

            if new_password != confirm_password:
                messages.success(request, 'Password did not match!')
                return redirect(f'/change-password/{token}/')

            user_obj = User.objects.get(id=user_id)
            user_obj.set_password(new_password)
            user_obj.save()
            return redirect('/login/')

    except Exception as e:
        print(e)
    return render(request, 'change-password.html', context)

# ForgetPassword view
def ForgetPassword(request):
    try:
        if request.method == 'POST':
            username = request.POST.get('username')

            if not User.objects.filter(username=username).first():
                messages.success(request, 'No user found with this username.')
                return redirect('/forget-password/')

            user_obj = User.objects.get(username=username)
            token = str(uuid4())
            student_profile_obj = StudentProfile.objects.get(user=user_obj)
            student_profile_obj.forget_password_token = token
            student_profile_obj.save()
            send_forget_password_mail(user_obj.email, token)
            messages.success(request, 'An email is sent.')
            return redirect('/forget-password/')

    except Exception as e:
        print(e)
    return render(request, 'forget-password.html')


from django.shortcuts import render, get_object_or_404
from .models import StudentProfile, StudentSubmission
from teachers.models import TestAssignment

from django.shortcuts import render, get_object_or_404
from .models import StudentProfile, TestAssignment, StudentSubmission
from grading_app.models import Assessment

def student_dashboard(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    assignments = TestAssignment.objects.filter(teacher=student.teacher)
    submissions = StudentSubmission.objects.filter(student=request.user)
    
    submitted_assignments = []
    not_submitted_assignments = []

    # Fetch submitted and not submitted assignments
    for submission in submissions:
        if submission.submitted:
            submitted_assignments.append(submission.test_assignment.assignment_id)
        else:
            not_submitted_assignments.append(submission.test_assignment.assignment_id)

    # Fetch assessments with grades for submitted assignments
    assessments_with_grades = {}
    for assignment_id in submitted_assignments:
        assessments = Assessment.objects.filter(teacher_assignment_file_id=assignment_id, grade__gt=0.0)
        if assessments.exists():
            assessments_with_grades[assignment_id] = assessments.first().grade

    context = {
        'student': student,
        'assignments': assignments,
        'submitted_assignments': submitted_assignments,
        'not_submitted_assignments': not_submitted_assignments,
        'assessments_with_grades': assessments_with_grades
    }
    return render(request, 'student_dashboard.html', context)

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import StudentSubmission


from django.shortcuts import get_object_or_404
from django.http import FileResponse
from .models import StudentSubmission

from django.shortcuts import render

# views.py



def view_all_student_submissions(request):
    assessments = Assessment.objects.all()
    context = {'assessments': assessments}
    #get the file path of teacher assignment depending on the modal clicked
    #langchain_integration(request,pdf_file_path)
    return render(request, 'view_all_student_submissions.html', context)


def view_submission(request, assignment_id):
    submission = get_object_or_404(StudentSubmission, test_assignment_id=assignment_id, student=request.user)
    # Assuming 'file' field in the StudentSubmission model stores the PDF file
    pdf_file = submission.file.path
    return FileResponse(open(pdf_file, 'rb'), content_type='application/pdf')

import os
from django.http import FileResponse
from django.conf import settings

def assignment_download(request, file_path):
    full_file_path = os.path.join(settings.BASE_DIR, file_path)
    return FileResponse(open(full_file_path, 'rb'))


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = StudentSubmission
        fields = ['file']
        labels = {'file': 'Upload your submission'}

    def clean_file(self):
        file = self.cleaned_data.get('file')

        return file

import os

def ocr_directory_path(instance, filename):
    directory_path = f'student_submissions/{instance.student.username}/{instance.test_assignment.assignment_id}/ocr/'
    os.makedirs(directory_path, exist_ok=True)
    
    return os.path.join(directory_path, filename)


def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(TestAssignment, pk=assignment_id)
    student = request.user
    test_assignment = assignment
    student_submission = StudentSubmission.objects.filter(student=student, test_assignment=test_assignment).first()
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES, instance=student_submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student = student
            submission.test_assignment = assignment
            submission.save()

            ocr_result = perform_ocr(submission, submission.file.path)
            if ocr_result:
                # Define the OCR file path using the ocr_directory_path function
                ocr_file_path = ocr_directory_path(submission, f'{student.username}_ocr.pdf')

                # Save the OCR result to a PDF file
                if save_to_pdf(ocr_result, ocr_file_path):
                    # Save the OCR file path to the submission
                    submission.ocr_file = ocr_file_path
                    submission.save()
                    messages.success(request, 'OCR conversion and assignment submission successful!')
                else:
                    messages.error(request, 'Failed to convert OCR result to PDF.')
            else:
                messages.error(request, 'OCR conversion failed, but assignment submitted successfully.')
            
            # Set graded to True when the submission is saved
            submission.submitted = True
            submission.save()

            return redirect('student_dashboard')
    else:
        form = SubmissionForm(instance=student_submission)

    return render(request, 'submit_assignment.html', {'form': form, 'assignment': assignment})



def preprocess_image(img):
    try:
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  
        _, processed_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
       
        return processed_img
    except Exception as e:
        print("Error during preprocessing:", e)
        return None


def perform_ocr(instance,pdf_file_path):
    try:
        ocr_results = []

        images = convert_from_path(pdf_file_path)

        for img in images:
            processed_img = preprocess_image(np.array(img))
            if processed_img is not None:
                _, output_file = cv2.imencode(".png", processed_img)
                content = output_file.tobytes()
                image = vision.Image(content=content)
                response = client.document_text_detection(image=image)
                docText = response.full_text_annotation.text
                ocr_results.append(docText)
            else:
                print("Preprocessing failed for page")
        return ocr_results
    except Exception as e:
        print("Error during OCR:", e)
        return None

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def save_to_pdf(text, path):
    try:
        c = canvas.Canvas(path, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica", 12)
        text = '\n'.join(text) if isinstance(text, list) else text

        lines = []
        for line in text.split('\n'):
            words = line.split()
            wrapped_lines = []
            while words:
                wrapped_line = ''
                while (words and c.stringWidth(wrapped_line + words[0]) < width - 100):
                    wrapped_line += words.pop(0) + ' '
                wrapped_lines.append(wrapped_line)
            lines.extend(wrapped_lines)

        y = height - 50  
        for line in lines:
            if y <= 50:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = height - 50
            c.drawString(50, y, line)
            y -= 15 
        c.save()
        return True
    
    except Exception as e:
        print("Error during PDF conversion:", e)
        return False
