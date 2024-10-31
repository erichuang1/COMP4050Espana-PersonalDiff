from flask import Blueprint, request, jsonify
from src.controllers.rubric_queries import *

rubric = Blueprint('rubric', __name__)

@rubric.route('/generate_rubric', methods=['POST'])
def generate_rubric():
    try:
        data = request.get_json()
        required_keys = ['staff_email', 'assessment_description', 'criteria', 'ulos']
        
        # Check if all required keys are present in data
        if not set(required_keys).issubset(data.keys()):
            return jsonify({'error': f"Missing required fields: {', '.join(required_keys)}"}), 400
        # Validate criteria structure
        criteria = data.get('criteria')
        required_criterion_subkeys = ['keywords', 'competencies', 'skills', 'knowledge']
        # Check if each criterion contains the required subkeys 
        for criterion in criteria:
            is_all_keys_available = set(required_criterion_subkeys).issubset(criterion.keys())
            if not is_all_keys_available:
                return jsonify({'error': f"Missing required fields in this criteria: {', '.join(required_keys)}"}), 400
        # Validate ULOs (ensuring that it is a non-empty list)
        ulos = data.get('ulos')
        if not ulos:
                return jsonify({'error': "ULOs list cannot be empty"}), 400
        # Call the controller
        response, status_code = create_rubric(data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while generating the rubric.", "error": str(e)}), 500

# Get generated rubric based on the rubric_title
@rubric.route('/rubric/<int:rubric_id>', methods=['GET'])
def get_generated_rubric(rubric_id):
    try:
        response, status_code = get_rubric(rubric_id)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving generated rubric.", "error": str(e)}), 500

# Update details about a generated rubric 
# Assuming that once user edits the Rubric Generated based on the AI output, frontend sends the entire edited rubric in JSON format to us
# This allows us to completely overwrite the existing rubric JSON in the file storing the JSON for that rubric with the new data.
# Also needs to regenerate the csv and pdf? Or create upon request and do not save
@rubric.route('/rubric/<int:rubric_id>', methods=['PUT'])
def update_rubric(rubric_id):
    try:
        data = request.get_json()
        if not data:
           return jsonify({"error": "No data provided"}), 400        
        response, status_code = update_rubric_changes(rubric_id, data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message:" f"An error occured while updating the rubric for {rubric_id}. "})        

# Route to delete a rubric
@rubric.route('/rubric/<int:rubric_id>', methods=['DELETE'])
def delete_rubric(rubric_id):
    try:
        response, status_code = delete_rubric_from_db(rubric_id) 
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": f"An error occurred while deleting the rubric {rubric_id}.", "error": str(e)}), 500


@rubric.route('/rubrics', methods=['GET'])
def get_all_rubrics():
    try:
        # Use request.args for GET requests to retrieve query parameters
        staff_email = request.args.get('staff_email')  # Query parameters for GET requests

        if not staff_email:
            return jsonify({"message": "Staff email not provided"}), 400

        # Call the actual function to retrieve units with the provided email
        response, status_code = fetch_all_rubrics(staff_email)  # Renamed to avoid recursion
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving the rubrics.", "error": str(e)}), 500

# Route to check if the rubric generation is complete 
@rubric.route('/job_status/<int:job_id>', methods=['GET'])
def check_job_status(job_id):
    try:
        response, status_code = get_job_status(job_id)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message: An error occured while getting the job status." "error": str(e)}), 500


# Route for downloading rubric for a rubric ID
@rubric.route('/download_rubric/<int:rubric_id>/<string:format>', methods=['GET'])
def download_rubric(rubric_id,format):
    try:
        return download_rubric_as(rubric_id, format)
    except Exception as e:
        return jsonify({"message: An error occured while generating rubric for downloading. " "error": str(e)}), 500