from flask import Blueprint, request, jsonify
from src.controllers.unit_queries import *

unit = Blueprint('unit', __name__)

# UA01: Route to create a new unit 
@unit.route('/units', methods=['POST'])
def add_unit():
    try:
        data = request.get_json()
        required_keys = ['unit_code', 'unit_name', 'convener_email', 'year','session', 'level']
        is_all_keys_available = set(required_keys).issubset(data.keys())
        if not is_all_keys_available :
            return jsonify({'error': f"Please provide {', '.join(required_keys)} "}), 400
        response, status_code = create_unit(data)  
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while creating the unit.", "error": str(e)}), 500

# UA01: Route to retrieve details of a specific unit
@unit.route('/units/<string:unit_code>', methods=['GET'])
def get_unit_details(unit_code):
    try:
        response, status_code = get_unit(unit_code)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": f"An error occurred while retrieving the unit details for {unit_code}.", "error": str(e)}), 500

# UA01: Route to update an existing unit (Frontend will only send us the unit detail that needs changing, not ALL the unit details)
@unit.route('/units/<string:unit_code>', methods=['PUT'])
def update_unit(unit_code):
    try:

        data = request.get_json()  
        # Check if data is None or empty
        if not data:
            return jsonify({"error": "No data provided"}), 400
        response, status_code = update_unit_details(unit_code, data)  
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": f"An error occurred while updating the unit {unit_code}.", "error": str(e)}), 500

# UA01: Route to delete a unit
@unit.route('/units/<string:unit_code>', methods=['DELETE'])
def delete_unit(unit_code):
    try:
        response, status_code = delete_unit_from_db(unit_code) 
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": f"An error occurred while deleting the unit {unit_code}.", "error": str(e)}), 500

# Endpoint to get all units 
@unit.route('/units', methods=['GET'])
def get_all_units_route():
    try:
        # Use request.args for GET requests to retrieve query parameters
        staff_email = request.args.get('staff_email')  # Query parameters for GET requests

        if not staff_email:
            return jsonify({"message": "Staff email not provided"}), 400

        # Call the actual function to retrieve units with the provided email
        response, status_code = fetch_all_units(staff_email)  # Renamed to avoid recursion
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving the units.", "error": str(e)}), 500

