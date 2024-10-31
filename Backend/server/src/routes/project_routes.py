from flask import Blueprint, request, jsonify
from src.controllers.project_queries import *

project = Blueprint('project', __name__)

# UA02: Route to create a new project within a unit
@project.route('/units/<string:unit_code>/projects', methods=['POST'])
def add_project(unit_code):
    try:
        data = request.get_json()
        required_keys = ['project_name'] 
        is_all_keys_available = set(required_keys).issubset(data.keys())
        if not is_all_keys_available :
            return jsonify({'error': f"Please provide {', '.join(required_keys)} "}), 400
        response, status_code = create_project(unit_code,data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({f"message": "An error occurred while creating the assignment.", "error": str(e)}), 500

# UA02: Route to retrieve details of a specific project within a unit
@project.route('/units/<string:unit_code>/projects/<string:project_title>', methods=['GET'])
def get_project(unit_code, project_title):
    try:
        response, status_code = get_project_details(unit_code, project_title)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving the assignment details.", "error": str(e)}), 500

# UA02: Route to update an existing project within a unit
@project.route('/units/<string:unit_code>/projects/<string:project_title>', methods=['PUT'])
def update_project(unit_code, project_title):
    try:
        data = request.get_json()
        required_keys = ['project_name']
        is_all_keys_available = set(required_keys).issubset(data.keys())
        if not is_all_keys_available :
            return jsonify({'error': f"Please provide {', '.join(required_keys)} "}), 400 
        response, status_code = update_project_details(unit_code, project_title, data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while updating the assignment.", "error": str(e)}), 500

# UA02: Route to delete a project within a unit
@project.route('/units/<string:unit_code>/projects/<string:project_title>', methods=['DELETE'])
def delete_project(unit_code, project_title):
    try:
        response, status_code = delete_project_from_db(unit_code, project_title)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while deleting the assignment.", "error": str(e)}), 500

# Route to add project questions template
@project.route('/units/<string:unit_code>/projects/<string:project_title>/template', methods=['POST'])
def add_project_questions_template(unit_code, project_title):
    try:
        data = request.get_json()

        required_keys = [
            'static_questions', 'question_bank_count', 'factual_recall_count', 'conceptual_understanding_count',
            'analysis_evaluation_count', 'application_problem_solving_count', 'open_ended_discussion_count', 
            'questions_difficulty']       
        
        is_all_keys_available = set(required_keys).issubset(data.keys())
        
        if not is_all_keys_available :
            return jsonify({'error': f"Please provide {', '.join(required_keys)} "}), 400
        response, status_code = create_project_questions_template(unit_code, project_title, data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({f"message":"An error occured while creating the questions template for {project_title}.", "error": str(e)}), 500

# Route to update project questions template
@project.route('/units/<string:unit_code>/projects/<string:project_title>/template', methods=['PUT'])
def update_project_questions_template(unit_code, project_title):
    try:
        # Get the data
        data = request.get_json()
        # Check if data is None or empty
        if not data:
            return jsonify({"error": "No data provided"}), 400
        response, status_code = update_questions_template(unit_code, project_title, data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({f"message:" "An error occured while updating the questions template for {project_title}. "})

# Route to get the project template
@project.route('/units/<string:unit_code>/projects/<string:project_title>/template', methods=['GET'])
def get_project_questions_template(unit_code, project_title):
    try:
        response, status_code = retrieve_questions_template(unit_code, project_title)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({f"message:" "An error occured while updating the questions template for {project_title}. "})

# Route to get all projects for a given unit 
@project.route('/units/<string:unit_code>/projects', methods=['GET'])
def get_all_projects_in_unit(unit_code):
    try:
        response, status_code = fetch_all_projects_from_unit(unit_code)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving all projects from this unit.", "error": str(e)}), 500
    
