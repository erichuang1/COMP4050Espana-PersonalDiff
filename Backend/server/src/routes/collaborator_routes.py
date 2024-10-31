from flask import Blueprint, request, jsonify
from src.controllers.collaborator_queries import *

collaborator = Blueprint('collaborator', __name__)

# UA03: Add collaborator for a specific unit 
@collaborator.route('/units/<string:unit_code>/collaborators', methods=['POST'])
def add_collaborator(unit_code):
    try:
        data = request.get_json()
        required_keys = ['staff_id', 'staff_name', 'role']
        is_all_keys_available = set(required_keys).issubset(data.keys())
        if not is_all_keys_available :
            return jsonify({'error': f"Please provide {', '.join(required_keys)} "}), 400
        response, status_code = add_collaborator_to_unit(unit_code, data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while adding the collaborator.", "error": str(e)}), 500

# UA04: Update the role of the collaborator 
@collaborator.route('/units/<string:unit_code>/collaborators', methods=['PUT'])
def assign_role(unit_code):
    try:
        data = request.get_json()
        required_keys = ['staff_id', 'staff_name', 'role']
        is_all_keys_available = set(required_keys).issubset(data.keys())
        if not is_all_keys_available :
            return jsonify({'error': f"Please provide {', '.join(required_keys)} "}), 400
        response, status_code = update_collaborator_role(unit_code, data)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while adding the collaborator.", "error": str(e)}), 500


# Get collaborator for unit
@collaborator.route('/units/<string:unit_code>/collaborators', methods=['GET'])
def get_collaborators(unit_code):
    try:
        response, status_code = get_collaborators_for_unit(unit_code)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving the collaborators for the unit.", "error": str(e)}), 500
    
# Get non collaborators for unit
@collaborator.route('/units/<string:unit_code>/non_collaborators', methods=['GET'])
def get_non_collaborators(unit_code):
    try:
        response, status_code = get_non_collaborators_for_unit(unit_code)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving the collaborators for the unit.", "error": str(e)}), 500
    
@collaborator.route('/staffs', methods=['GET'])
def get_all_staffs_list():
    try:
        response, status_code = get_all_staff()
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": "An error occurred while retrieving all the collaborators.", "error": str(e)}), 500
    
@collaborator.route('/units/<string:unit_code>/collaborators/<int:staff_id>', methods=['DELETE'])
def delete_collaborator(unit_code, staff_id):
    try:
        response, status_code = delete_collaborator_for_unit(unit_code, staff_id) 
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"message": f"An error occurred while deleting the colloaborator.", "error": str(e)}), 500
