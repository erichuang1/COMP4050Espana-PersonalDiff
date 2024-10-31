from flask import Blueprint, request, jsonify
from src.controllers.qbank_queries import *

# Create a Blueprint for the question bank
question_bank = Blueprint('question_bank', __name__)

# Route to upload questions to the question bank
@question_bank.route('/units/<string:unit_code>/projects/<string:project_title>/question_bank', methods=['POST'])
def upload_questions(unit_code, project_title):
    # Check if a file is part of the request
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    
    file = request.files['file']

    # Check if a file is uploaded
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    try:
        response, status = add_questions(unit_code, project_title, request)
        return jsonify(response), status
    except Exception as e:
        return jsonify({"message": "An error occurred while uploading the questions.", "error": str(e)}), 500

# Route to retrieve questions from the question bank
@question_bank.route('/units/<string:unit_code>/projects/<string:project_title>/question_bank', methods=['GET'])
def retrieve_questions(unit_code, project_title):
    try:
        response, status = retrieve_questions_from_db(unit_code, project_title)
        return jsonify(response), status
    except Exception as e:
        return jsonify({"message": "An error occurred while uploading the questions.", "error": str(e)}), 500
