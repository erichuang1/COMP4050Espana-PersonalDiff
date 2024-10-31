from flask import Blueprint, request, jsonify
from src.controllers.student_queries import *

student = Blueprint('student', __name__)

# UB03: Route to upload student details for a specific unit 
@student.route('/units/<string:unit_code>/students', methods=['POST'])
def add_students_info(unit_code):
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    
    file = request.files.get('file')

    # Check if a file was uploaded
    if file is None or file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    try:
        response, status_code = upload_student_csv(unit_code,request)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while uploading student details.", "error": str(e)}), 500

# UA07: Route to retrieve a list of students within a unit 
@student.route('/units/<string:unit_code>/students', methods=['GET'])
def get_students_list(unit_code):
    try:
        response, status_code = fetch_students_list(unit_code)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving the student list.", "error": str(e)}), 500

# UB08: Route to assign students to specific question PDFs #TODO
@student.route('/units/<string:unit_code>/projects/<string:project_title>/assign_questions', methods=['POST'])
def assign_questions(unit_code, project_title):
    pass

