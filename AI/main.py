from multiprocessing import process # ?
from openai import OpenAI
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request
from pydantic import BaseModel # ?
import re
import os
# import requests # -- used in test_client
import pymupdf


app = Flask(__name__)
load_dotenv() # Loading env file for future data retrieval

# VERY IMPORTANT PLEASE IMPLEMENT VARIABLES IN ENV FILE AS NAMED HERE:
client = OpenAI( 
  api_key= os.getenv("OPENAI_API_KEY"),  
  organization= os.getenv("OPENAI_ORG_KEY"),
  project= os.getenv("OPENAI_PROJ_KEY")  
)

# Configuring File upload settings:
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# checks if the uploaded file has an allowed extension.
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract text from PDF --> Need error checking functions here please
def extract_text_from_pdf(pdf_path):
    # reader = PdfReader(pdf_path) #This one seems to print every word on a new line?
    # text = ""
    # for page in reader.pages:
    #     text += page.extract_text()
    # return text
    
    doc = pymupdf.open(pdf_path) # open a document
    text = ""
    for page in doc: # iterate the document pages
        text += page.get_text() # get plain text encoded as UTF-8
    return text

def batch_process_files(pdf_files):
    results = {}
    for pdf_file in pdf_files:
        text = extract_text_from_pdf(pdf_file)
        questions = generate_viva_questions(text)
        results[pdf_file] = questions
    return results

# Batch Processing: Needs OpenAI BATCH API implementation
@app.route('/upload', methods=['POST']) # Define the route and the accepted HTTP method
def upload_files():
    if 'files[]' not in request.files:  # Return an error if no files were part of the request
        return jsonify({"error": "No files part in the request"}), 400
    
    files = request.files.getlist('files[]')
    
    if len(files) == 0:  # Return an error if no files were selected for uploading
        return jsonify({"error": "No files selected for uploading"}), 400
    
    file_paths = []
    
    for file in files:  # Save each uploaded file to the /tmp directory
        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)
        file_paths.append(file_path)
    
    results = batch_process_files(file_paths)  # Process the files in batch
    
    return jsonify(results)  # Return the results as a JSON response

# AN EXAMPLE OF WHAT THE USER_REQ JSON PAYLOAD MAY LOOK LIKE:
test_user_req = {
    "assignment_title" : "Impact of Agile Methodologies on Software Development", #Change this to add assignment title to prompt
    "unit_name" : "Introduction to Software Engineering", #Change this to add unit title to prompt
    "no_of_questions" : 3, #Change this to add no.of questions to prompt
    "question_challenging_level" : "Medium", #Change this to add medium, hard, challenging level to promp
    "assignment_content" : "TEST" #To be changed to incorporate a PDF file.
}

# Defining endpoint to generate questiongen responses:
@app.post("/generatequestions")
def generate_viva_questions():

    ###NEED TO IMPLEMENT VSALIDATION OF ALL VARIABLES IN THE REQUEST PAYLOAD (CHECKING IF THEY ARE ALL PROVIDED, MEET REQ)
    job_id = request.form.get("job_id")
    # No file provided
    if 'file' not in request.files:
        return jsonify({"error": "No file part",
                        "job_id": job_id}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file",
                        "job_id": job_id}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Get form data
        assignment_title = request.form.get("assignment_title")
        unit_name = request.form.get("unit_name")
        no_of_questions = request.form.get("no_of_questions")
        question_challenging_level = request.form.get("question_challenging_level")
        student_year_level = request.form.get("student_year_level")
        
        # Validate all required fields are present
        if not all([assignment_title, unit_name, no_of_questions, question_challenging_level]):
            return jsonify({"error": "Missing required fields",
                            "job_id": job_id}), 400
        
        assignment_content = extract_text_from_pdf(file_path)

        test_prompt = f""" 
        You are Professor Alex Chen, a renowned expert in {unit_name} with 20 years of experience in conducting oral examinations. Your rigorous yet fair questioning style is known to thoroughly assess students' understanding.

        Assignment Details:
        Title: {assignment_title}
        Unit: {unit_name}
        Student Year Level: {student_year_level}

        Your task is to create {no_of_questions} oral examination questions that rigorously test the student's understanding and knowledge of the subject matter. Each question should be {question_challenging_level}.
        When generating questions, focus on assessing these three key areas:

        - Familiarity: Is the student familiar with the content as written?
        - Discussion Proficiency: Can the student engage in a meaningful conversation about the concepts presented?
        - Critical Expansion: Can the student expand upon the assignment's content by exploring related ideas and concepts?

        Include a mix of the following question types, aligned with appropriate levels of Bloom's taxonomy:
        - Factual recall questions
        - Conceptual understanding questions
        - Analysis and evaluation questions
        - Application and problem-solving questions
        - Open-ended discussion questions

        Remember to maintain your reputation for comprehensive and insightful questioning. Your questions should not only test the student's knowledge of the assignment content but also their ability to think critically about the subject and apply concepts to new situations. Pay special attention to key themes, methodologies, and arguments presented in the assignment.
        Present the questions in the following JSON format: {{question_X:...., question_X:.....}} where X is the question number

        Analyze the assignment content provided at the end of this prompt thoroughly to ensure that your questions are directly relevant and appropriately challenging for a university-level oral examination.
        Assignment Content: 

        {assignment_content}
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                # {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": test_prompt}
            ],
            max_tokens=800,
            response_format={"type": "json_object"} # Specifying response type as JSON
        )

        response = completion.choices[0].message.content
        print("Assignment content: " + assignment_content)

        print(response)
    
        # Clean up: remove the uploaded file
        os.remove(file_path)

        # Return the generated questions
        return jsonify({"success": response,
                        "job_id": job_id}), 200

    return jsonify({"error": "Invalid file type",
                    "job_id": job_id}), 400

# Route to regenerate questions based on user feedback
@app.post("/regeneratequestions")
def regenerate_questions():
    job_id = request.form.get("job_id")

    # No file provided
    if 'file' not in request.files:
        return jsonify({"error": "No file part", "job_id": job_id}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file", "job_id": job_id}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
    else:
        return jsonify({"error": "Good luck!", "job_id": job_id}), 400
    
    assignment_content = extract_text_from_pdf(file_path)

# -- removed --
    # # List of questions to regenerate
    # selected_questions = request.form.getlist("selected_questions[]")

    # # Reason from dropdown
    # regen_reasons = request.form.getlist("regen_reasons[]")  
# --

    # Example format of question_reason input: 
    # [{'question': 'Question 1', 'reason': 'Too vague'}, {'question': 'Question 2', 'reason': 'Not aligned with content'}]
    
    # List of questions and asociated reasons (key-value pair)
    question_reason = request.form.getlist("question_reason[]")

    # Assignment details
    assignment_title = request.form.get("assignment_title")
    unit_name = request.form.get("unit_name")

    # Validate assignment fields
    if not all([assignment_title, unit_name, question_reason]):
        return jsonify({"error": "Missing required fields", "job_id": job_id}), 400

    # Regen Promt
    regen_prompt = f"""
    As a University Professor teaching {unit_name}, a student has submitted their assignennt for {assignment_title}.
    The following questions have been flagged for regeneration based on user feedback:
    """
# -- removed --
    # for i, (question, reason) in enumerate(zip(selected_questions, regen_reasons), 1):
    #     regen_prompt += f"\nquestion {i}: {question}\nreason: {reason}\n"
# --
    for i, item in enumerate(question_reason, 1):
        question = item.get('question')
        reason = item.get('reason')
        if question and reason:
            regen_prompt += f"\nquestion {i}: {question}\nreason: {reason}\n"
        else:
            return jsonify({"error": "Each question must have an associated reason.", "job_id": job_id}), 400
    
    regen_prompt += f"""
    Please regenerate these questions for to access the student while ensuring that the new questions address the concerns raised and fit within the context of the assignment content below.
    {assignment_content}
    """

    # OpenAI API Call for question regeneration
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": regen_prompt}
        ],
        max_tokens=800,
        response_format={"type": "json_object"}
    )
    
    response = completion.choices[0].message.content
    
    # Output
    print("Assignment content: " + assignment_content)
    print(response)
    
    # Clean up: remove the uploaded file
    os.remove(file_path)

    return jsonify({"regenerated_questions": response, "job_id": job_id}), 200

## -- Regen Reasons --
    # "Too vague"
    # "Too difficult for the given level"
    # "Not aligned with assignment content"
    # "Repetitive or redundant"
    # "Lack of critical thinking assessment"
    # "Grammatical or phrasing issues"
    # "Not challenging enough"
## --

# Base endpoint for Grammar Evaluation Module
@app.route('/api/grammar/evaluate', methods=['POST'])
def evaluate_grammar():
    # Placeholder for future development
    return jsonify({"message": "Grammar Evaluation Endpoint - Ready for future implementation"}), 200

# Base endpoint for Marking Rubric Generation Module
@app.route('/api/rubric/generate', methods=['POST'])
def generate_rubric():
    # Placeholder for future development
    return jsonify({"message": "Marking Rubric Generation Endpoint - Ready for future implementation"}), 200

# IF YOU ARE TESTING THIS LOCALLY PLEASE DELETE HOST PARAMETER BELOW. 
# Make sure to put it back in when you push
if __name__ == "__main__":
    app.run(host= '0.0.0.0',debug=True) 
    # app.run() 