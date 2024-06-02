# Automated Paper Checking System
### Semester VI Project
- Lisa James Gonsalves (9607)
- Crystal Elaine Fernandes (9539)
- Saahil Fernandes (9540)
- Eden Evelyn Charles (9593)

## Module Description
The system comprises the following components:

**Dashboard:**

The main user interface providing educators with an overview of grading tasks, student results, and relevant information.

Separate sections for Teacher Dashboard and Student Dashboard catering to specific needs.

**External Services:**

Utilizes cloud-based services for processing answer sheets.

**Google Cloud Vision API:** Used for optical character recognition (OCR) to convert handwritten text into digital text.

**Langchain Framework:** Framework employing a large language model (LLM) to process extracted text and assess answer sheets against model answers.

## Implementation
**Module 1:** Detection of Handwriting and Conversion to Text
- Teacher uploads question paper and model answer sheet.
- The student uploads their answer sheet in a handwritten format.
- Google Cloud Vision converts handwritten content into digital text.
- Ensures accurate transcription of handwritten answers into PDF format.

**Module 2:** Checking the Answers
Handwritten answers are transformed into digital text.
Large Language Model (LLM) evaluates student responses against model answers.
Utilizes advanced natural language processing techniques for objective grading.
Grading is done based on the maximum grade allocated for each question.

**Module 3:** Grading and Feedback
- Using Langchain and LLM we generate comprehensive feedback tailored to each student's performance.
- Includes assigned grades, insights on areas of improvement, and suggestions for enhancement.
- Promotes continuous learning and improvement.

## Video Demo

https://github.com/CrystalEFernandes/automatedPaperChecking/assets/68494281/b4918b49-ed1e-4c11-9d47-b0daa23f5647

## Project Report
[TE Mini Project Report.pdf](https://github.com/user-attachments/files/15526321/TE.Mini.Project.Report.pdf)

## Marking for Low Quality Answer Example

https://github.com/CrystalEFernandes/automatedPaperChecking/assets/68494281/e32b9080-df1c-4ae6-855f-79ab16293c44


## Marking for A Good Answer Example

https://github.com/CrystalEFernandes/automatedPaperChecking/assets/68494281/23c2ca82-e970-43b4-aad1-bf0e674f46ee

