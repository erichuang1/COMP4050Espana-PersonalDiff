from flask import Blueprint, jsonify
from src.controllers.question_generation_queries import *
import traceback
question = Blueprint('question', __name__)

# U-B05 (task 2): Route to generate questions for ALL SUBMISSIONS
@question.route('/units/<string:unit_code>/projects/<string:project_title>/generate_questions', methods=['POST'])
def generate_questions_for_all(unit_code, project_title):
    try:
        response, status_code = generate_for_all(unit_code, project_title)
        return jsonify(response), status_code
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "An error occurred while generating questions for all Submissions.", "error": str(e)}), 500
    
# Route to generate questions for specific submission
@question.route('/units/<string:unit_code>/projects/<string:project_title>/generate_questions/<int:submission_id>', methods=['POST'])
def generate_questions_for_one(unit_code, project_title, submission_id):
    print("HIMA - question generate")
    try:
        response,status_code = generate_for_submission(unit_code, project_title, submission_id) 
        return jsonify(response), status_code
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message: An error occured while  generating questions for the submission." "error": str(e)}), 500

# U-B06: Route to re-generate questions for a specific submission 
@question.route('/units/<string:unit_code>/projects/<string:project_title>/re_generate_questions/<int:submission_id>', methods=['POST'])
def regenrate_question_for_one(unit_code, project_title, submission_id):
    try:
        data = request.get_json()
        response,status_code = regenerate_questions(unit_code, project_title, submission_id, data) 
        return jsonify(response), status_code
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message: An error occured while re-generating questions for the submission." "error": str(e)}), 500

# Get generated questions for SINGLE SUBMISSION
@question.route('/questions/<int:submission_id>', methods=['GET'])
def get_generated_questions(submission_id):
    try:
        response, status_code = get_questions_for_submission(submission_id)
        return jsonify(response), status_code
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "An error occurred while retrieving generated questions for the submission.", "error": str(e)}), 500

# Route to check if the queston generation is complete 
@question.route('/job_status/<int:job_id>', methods=['GET'])
def check_job_status(job_id):
    try:
        response, status_code = get_job_status(job_id)
        return jsonify(response), status_code
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message: An error occured while getting the job status." "error": str(e)}), 500

# U-B09: Route for downloading questions PDF for a submission ID
@question.route('/download_questions/<int:submission_id>', methods=['GET'])
def download_questions_pdf(submission_id):
    try:
        response, status_code = download_questions(submission_id)
        return jsonify(response), status_code
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message: An error occured while getting the job status." "error": str(e)}), 500