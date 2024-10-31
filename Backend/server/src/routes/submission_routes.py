import traceback
from flask import Blueprint, request, jsonify
from src.controllers.submission_queries import *

submission = Blueprint('submission', __name__)

# UB02 : Route to upload submissions for a project within a unit -> batch upload 
@submission.route('/units/<string:unit_code>/projects/<string:project_title>/files', methods=['POST'])
def upload_files_in_project(unit_code, project_title):
    staff_email = request.form.get('staff_email') # Receiving simple data
    if not staff_email:
        return jsonify({"message": "Uploader staff email not provided"}), 400
    if 'files[]' not in request.files:
        return jsonify({"message": "No files part in the request"}), 400
    
    files = request.files.getlist('files[]') # Receiving binary data

    if not files:
        return jsonify({"message": "No files selected"}), 400
    try:
        response, status_code = batch_upload_pdfs(unit_code, project_title, staff_email, files)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while uploading the PDFs.", "error": str(e)}), 500

# UB04: Route to get all files for a project within a unit 
@submission.route('/units/<string:unit_code>/projects/<string:project_title>/files', methods=['GET'])
def get_files_in_project(unit_code, project_title):
    try:
        response, status_code = get_list_of_submission_files(unit_code, project_title) 
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving files for the Project.", "error": str(e)}), 500

# UA05: Route to delete all PDFs within projects 
@submission.route('/units/<string:unit_code>/projects/<string:project_title>/files', methods=['DELETE'])
def delete_files_in_project(unit_code, project_title):
    try:
        response, status_code = delete_all_files(unit_code, project_title) 
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while deleting files from the Project.", "error": str(e)}), 500

# UA06: Route to delete specific PDF within the project 
@submission.route('/units/<string:unit_code>/projects/<string:project_title>/files/<int:submission_id>', methods=['DELETE'])
def delete_file(unit_code, project_title, submission_id):
    try:
        response, status_code = delete_file_from_db(unit_code, project_title, submission_id)
        return jsonify(response), status_code
    except Exception as e:
        traceback.print_exc()
        return jsonify({"message": "An error occured while deleting this file.", "error" : str(e)}), 500 