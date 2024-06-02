from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import pandas as pd
import time

def get_marking_scheme(pdf_docs):
    marking_scheme_list = []  # List to store individual marking schemes
    stop_word = "DONE"  # Define the stop word
    start_pattern = re.compile(r'\d+\)')  # Regular expression pattern to match numbers followed by a closing parenthesis

    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)

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

def get_answer(pdf_docs):
    answers_list = []  # List to store individual answers
    stop_word = "STOP"  # Define the stop word

    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)

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

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    You are a teacher grading a student's assignment.  You will be provided with two pdf files containing the question and answers.  Your task is to analyze the student's answer compared to the model answer key.
    Adhere to the evaluation criteria.

    Evaluation Criteria:
    Accuracy: Does the student's answer factually correct and consistent with the key concepts?
    Understanding: Does the answer demonstrate a grasp of the relevant concepts and ideas?
    Clarity: Is the answer well-organized, easy to follow, and uses clear language?
    Completeness: Does the answer address all/enough key points of the question?
    Relevance: Does the answer stay focused on the topic and avoid irrelevant information?
    Keywords: Does the answer include important keywords and terminology from the subject area?
    Appropriate Information: Does the answer use appropriate information and examples(only if needed) to support the main points?

    Analysis and Feedback:
    Provide a detailed analysis of how the student's answer can be improved according to the evaluation criteria above.  Be specific and actionable in your feedback.  For each area assessed (e.g., Accuracy, Clarity), explain how the student's answer could be better and why that improvement is important.

    Grading:
    Assign a grade based on your analysis, taking into account all the evaluation criteria.  Justify the grade by explaining how well the student's answer meets the expectations outlined in the model answer key.
    Grading should be based solely on the information provided in the two pdf files.
    If the student makes a minor mistake do not cut marks for the same.
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

def user_input(matched_dict):
    feedback_dict = {}  # Dictionary to store feedback for each question
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

    for student_answer, marking_scheme in matched_dict.items():
        docs = new_db.similarity_search(student_answer)

        chain = get_conversational_chain()
        response = chain({
            "input_documents": docs,  # Pass the marking scheme chunks
            "question": student_answer,  # Use the student's answer as the question
        }, return_only_outputs=True)

        # Store the feedback for each question in the dictionary
        feedback_dict[student_answer] = response["output_text"]

    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(feedback_dict.items(), columns=['Question', 'Feedback'])

    # Write DataFrame to Excel file
    df.to_excel('feedback.xlsx', index=False)

    # Optionally return the DataFrame
    return df
