from flask import Blueprint, request, jsonify
from src.controllers.marking_guide_queries import *

marking_guide = Blueprint('marking_guide', __name__)

# U-D01 : Endpoint to upload marking guide
# Upload a pdf file (1 marking guide file) of an existing marking guide into the application along with text inputs
@marking_guide.route('/marking_guide', methods=['POST'])
def upload_marking_guide():
    staff_email = request.form.get('staff_email') # Receiving simple data
    if not staff_email:
        return jsonify({"message": "Marking guide ploader staff email not provided"}), 400
    # Check if a file is present in the request
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400

    # Retrive the file from the request 
    file = request.files['file']

    # Check if a file is selected
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400
    try:
        response, status_code = upload_marking_guide_to_db(staff_email, file)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while uploading the PDF file for marking guide.", "error": str(e)}), 500

# U-D04 : Endpoint to convert the uploaded marking guide into a rubric
@marking_guide.route('/convert_marking_guide/<int:marking_guide_id>', methods=['POST'])
def convert_marking_guide(marking_guide_id):
    data = request.get_json()
    required_keys = ['staff_email', 'ulos']
    is_all_keys_available = set(required_keys).issubset(data.keys())
    if not is_all_keys_available :
        return jsonify({'error': f"Please provide {', '.join(required_keys)} "}), 400
    try:
        response, status_code = generate_marking_guide_rubric(marking_guide_id, data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while generating the rubric for marking guide.", "error": str(e)}), 500


