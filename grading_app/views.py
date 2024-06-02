from django.shortcuts import render
from django.core.files.storage import default_storage
from django.http import HttpResponse
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from teachers.models import TestAssignment
from students.models import StudentSubmission
from .models import Assessment
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def perform_tfidf_and_matching(marking_scheme_list, answers_list):
    # Perform TF-IDF vectorization
    vectorizer = TfidfVectorizer()
    all_text = marking_scheme_list + answers_list
    tfidf_matrix = vectorizer.fit_transform(all_text)

    # Calculate cosine similarity
    similarity_matrix = cosine_similarity(tfidf_matrix[-len(answers_list):], tfidf_matrix[:-len(answers_list)])

    # Find the best matching marking scheme for each answer
    best_matches = {}
    for i, answer in enumerate(answers_list):
        best_match_index = similarity_matrix[i].argmax()
        best_matches[answer] = marking_scheme_list[best_match_index]

    # Convert the matched pairs into a dictionary
    matched_dict = {answer: marking for answer, marking in best_matches.items()}

    return matched_dict

def get_pdf_text(pdf_file):
    text = ""
    with default_storage.open(pdf_file, 'rb') as file:
        pdf_reader = PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n\n"  # Add a newline between pages
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
    chunks = text_splitter.split_text(text)
    return chunks

def get_answer(pdf_file):
    answers_list = []  # List to store individual answers
    stop_word = "STOP"  # Define the stop word

    with default_storage.open(pdf_file, 'rb') as file:
        pdf_reader = PdfReader(file)

        for page_number, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()

            # Regular expression pattern to match numbers followed by a closing parenthesis
            pattern = re.compile(r'(\d+)\)')
            # Find all matches of the pattern in the text
            matches = pattern.finditer(text)

            # Iterate over the matches and extract the corresponding text
            for match in matches:
                answer_number = match.group(0)
                start_index = match.end()

                # Find the end of the current answer
                end_index = text.find(stop_word, start_index)
                if end_index == -1:
                    end_index = len(text)

                # Extract the current answer
                answer_text = text[start_index:end_index].strip()
                answers_list.append(answer_text)

    return answers_list

def get_marking_scheme(pdf_file):
    marking_scheme_list = []  # List to store individual marking schemes
    stop_word = "DONE"  # Define the stop word
    start_pattern = re.compile(r'\d+\)')  # Regular expression pattern to match numbers followed by a closing parenthesis

    with default_storage.open(pdf_file, 'rb') as file:
        pdf_reader = PdfReader(file)

        for page_number, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()

            # Find all matches of the start pattern in the text
            start_matches = start_pattern.finditer(text)

            for start_match in start_matches:
                start_index = start_match.start()
                end_index = text.find(stop_word, start_index)
                if end_index != -1:
                    # Extract the current answer
                    answer_text = text[start_index:end_index].strip()
                    marking_scheme_list.append(answer_text)  # Add answer to the main list
                else:
                    # If stop word not found after start pattern, skip this match
                    continue

    return marking_scheme_list

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    Compare and analyze the two documents. 
    The first document is the teachers document.
    The second document is the students document.
    base the teachers document on maximum marks provided in the bracket. And compare the student document to it.
    If major differences are there in the student and teacher document, cut marks and reduce the grade.
    Evaluate based on differences in keywords, completeness, concept and understanding.
    Accordingly give marks.

    Grading should be based solely on the information provided in the two pdf files.    
    Do mention why they did not score full marks and areas of improvement in comparison to the marking scheme.
    Do not cut marks for organization of content.
    Give the grade in the format of Grade:_/(maximum grade provided) 

    Context:
    {context}?

    Question:
    {question}

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro",
                                   temperature=0.3)

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain

def assess_pdf_files(marking_scheme_pdf, answers_pdf):
    matched_dict = {}  # Define matched_dict outside the if block

    # Get marking scheme text from PDF file
    marking_scheme_list = get_marking_scheme(marking_scheme_pdf)

    # Get answers from PDF file
    answers_list = get_answer(answers_pdf)

    if marking_scheme_list and answers_list:
        # Perform TF-IDF vectorization and generate matched pairs dictionary
        matched_dict = perform_tfidf_and_matching(marking_scheme_list, answers_list)

    # Convert values of matched_dict to a single string
    marking_scheme_text = "\n\n".join(matched_dict.values())
    marking_scheme_chunks = get_text_chunks(marking_scheme_text)
    get_vector_store(marking_scheme_chunks)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

    # Store individual feedback responses
    feedback_responses = []

    for student_answer, marking_scheme in matched_dict.items():
        docs = new_db.similarity_search(marking_scheme)
        chain = get_conversational_chain()
        response = chain({
            "input_documents": docs,  # Pass the marking scheme chunks
            "question": student_answer,  # Use the student's answer as the question
            "context": f"This is the student answer:{student_answer}\n This is the true teachers answer{marking_scheme}"
        }, return_only_outputs=True)
        feedback_responses.append(response["output_text"])

    # Concatenate all feedback responses into a single string
    final_feedback = "\n\n".join(feedback_responses)

    return final_feedback

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from students.models import StudentSubmission

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from students.models import StudentSubmission
from grading_app.models import Assessment
from teachers.models import TestAssignment
from grading_app.views import assess_pdf_files
import os
  
from dotenv import load_dotenv

def activate_grading_app_ungraded(request, assignment_id):
    # Get the assignment
    assignment = get_object_or_404(TestAssignment, pk=assignment_id)

    # Get ungraded submissions related to the assignment
    ungraded_submissions = StudentSubmission.objects.filter(test_assignment=assignment, graded=False)
    
    # Iterate over each ungraded submission
    for submission in ungraded_submissions:
        # Get the OCR file path for the submission
        ocr_filepath = submission.ocr_file.path if submission.ocr_file else None
        
        print("OCR File Path:", ocr_filepath)  # Debug statement

        # Get the absolute file path for the marking scheme PDF
        marking_scheme_pdf = assignment.file.path
        
        print("Marking Scheme PDF File Path:", marking_scheme_pdf)  # Debug statement

        # Assess the submission using the grading app functionality
        feedback = assess_pdf_files(marking_scheme_pdf, ocr_filepath)
        
        print("Feedback:", feedback)  # Debug statement

        grade=extract_grade(feedback)
        # Create an entry in the database for the assessment response
        assessment = Assessment.objects.create(
            teacher_assignment_file=assignment,
            student_assignment_submission_file=submission,
            response=feedback,
            grade=grade,
        )
        assessment.save()
        submission.graded = True
        submission.save()

    # Optionally, you can add a success message
    messages.success(request, 'Grading app activated for ungraded submissions.')

    # Redirect back to the view_student_submissions page
    return redirect('view_student_submissions', assignment_id=assignment_id)

# while rendering process

import re

import re

def extract_grade(feedback_response):
    # Define a regular expression pattern to match the grade
    grade_pattern = re.compile(r'Grade: (\d+(\.\d+)?)\/(\d+)')

    # Use findall to extract all matches of the grade pattern
    grades = grade_pattern.findall(feedback_response)

    # Initialize variables to calculate total grade
    total_grade = 0
    total_max_grade = 0

    # Iterate over extracted grades and calculate total grade
    for grade in grades:
        grade_value = float(grade[0])
        max_grade = int(grade[2])
        total_grade += grade_value
        total_max_grade += max_grade

    # Calculate the final grade
    if total_max_grade == 0:
        return 0.0
    else:
        final_grade = (total_grade / total_max_grade) * 100
        return final_grade


