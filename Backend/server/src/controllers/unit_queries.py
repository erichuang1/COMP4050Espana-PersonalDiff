from sqlalchemy import select

from src.db_instance import db
from src.models.models_all import *
import src.file_management as fm

def create_unit(data):
    """
    Create a new unit in the database if it doesn't already exist.
    :param data: unit details (unit_code, unit_name, convener_email, year, session )
    :return: JSON object with details of the created unit or an error message

    """
    unit_code = data.get('unit_code')
    unit_name = data.get('unit_name')
    convener_email = data.get('convener_email')
    unit_year = data.get('year')
    unit_session = data.get('session')
    unit_level = data.get('level')

    # Look up the convener using convener_email and see if they exist / have logged/signed into application before
    existing_convener = db.session.execute(select(Staff).filter_by(staff_email=convener_email)).scalar_one_or_none()
    if existing_convener is None:
        return{f"message": "Convener with email {convener_email} not found"}, 404
    # Get staff_id of convener
    convener_staff_id = existing_convener.staff_id
    # Check if the unit already exists
    existing_unit = Unit.query.filter_by(unit_code=unit_code).first()
    if existing_unit:
        return {"message": "Unit with this code already exists"}, 400
    
    # Create a new unit
    new_unit = Unit(
        unit_code = unit_code,
        unit_name = unit_name,
        convener_id = convener_staff_id,
        unit_year = unit_year,  
        unit_session = unit_session, 
        unit_level = unit_level
    )

    try:
        db.session.add(new_unit)
        db.session.commit()
        return {
            "unit_code": new_unit.unit_code,
            "unit_name": new_unit.unit_name,
            "year": new_unit.unit_year,  
            "session": new_unit.unit_session,
            "level": new_unit.unit_level
        }, 201
    except Exception as e:
        db.session.rollback()
        return {"message": "Failed to create unit", "error": str(e)}, 500

def get_unit(unit_code):
    """
    Retrieve details of a specific unit by its unit_code.

    :param unit_code: The unit_code of the unit to retrieve
    :return: JSON object with unit details or an error message
    """
    # Retrieve unit
    unit = db.session.execute(select(Unit).filter_by(unit_code=unit_code)).scalar_one_or_none()

    # If the unit does not exist, return an error message
    if unit is None:
        return {"message": "Unit not found"}, 404
    
    # If the unit exists, return its details
    return {
        "unit_code": unit.unit_code,
        "unit_name": unit.unit_name,
        "convener_id": unit.convener_id,
        "year": unit.unit_year,
        "session": unit.unit_session,
        "level": unit.unit_level
    }, 200

def update_unit_details(unit_code, data):
    """
    Update details of an existing unit.

    :param unit_code: The unit_code of the unit to update
    :param data: Dictionary containing updated unit details
    :return: JSON object with updated unit details or an error message
    """
    # Retrieve unit
    unit = db.session.execute(select(Unit).filter_by(unit_code=unit_code)).scalar_one_or_none()

    # If the unit does not exist, return error message
    if unit is None:
        return {"message": "Unit not found"}, 404
    
    # Update the unit fields if provided in the data
    if 'unit_name' in data:
        unit.unit_name = data['unit_name']
    if 'year' in data:
        unit.unit_year = data['year']
    if 'session' in data:
        unit.unit_session = data['session']
    if 'level' in data:
        unit.unit_level = data['level']

    try:
        db.session.commit()
        # JSON response with updated unit details and a success message
        response = {
            "message": "Unit updated successfully",
            "unit": {
                "unit_code": unit.unit_code,
                "unit_name": unit.unit_name,
                "convener_id": unit.convener_id,
                "year": unit.unit_year,
                "session": unit.unit_session,
                "level":unit.unit_level
            }
        }
        return response, 200
    except Exception as e:
        # In case of any errors, rollback the transaction and return an error message
        db.session.rollback()
        return {"message": "An error occurred while updating the unit", "error": str(e)}, 500

def delete_unit_from_db(unit_code):
    """
    Delete a specific unit by its unit_code.

    :param unit_code: The unit_code of the unit to delete
    :return: message for success or failure
    """
    try:
        # Step 1: Retrieve unit
        unit = db.session.execute(select(Unit).filter_by(unit_code=unit_code)).scalar_one_or_none()
        
        # If the unit does not exist, return an error message
        if unit is None:
            return {"message": "Unit not found"}, 404
        
        # Step 2: Retrieve all the projects for the unit
        projects = db.session.execute(select(Project).filter_by(unit_code=unit_code)).scalars()

        # Step 3: Iterate through each project for the unit
        for project in projects:
            # Step 3a: Retrieve all the submssions for the project
            submissions = db.session.execute(select(Submission).filter_by(project_id=project.project_id)).scalars()
            # Step 3b: For each submission, get the all questions generated
            for submission in submissions:
                # Step 3c:  Retrieve all the question generated files for the submission
                generated_qn_files = db.session.execute(select(GeneratedQnFile).filter_by(submission_id=submission.submission_id)).scalars()
                # Step 3d: Delete the file, using file system management
                for generated_qn_file in generated_qn_files:
                    file_status = fm.del_file(generated_qn_file.generated_qn_file_name)

                    if file_status == fm.FileStatus.OKAY:
                        print(f"File deleted successfully.")
                    else:
                        print(f"Failed to delete file. Status: {file_status.name}")
                        # Step 7: Delete the file details from the database
                    db.session.delete(generated_qn_file)
                # Step 3e: Delete the submission 
                db.session.delete(submission)

            # Step 4: Delete the project from the database
            db.session.delete(project)
        # Step 5: Delete the unit from the database
        db.session.delete(unit)
        db.session.commit()
        
        # Return a success message
        return {"message": "Unit deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while deleting the unit.", "error": str(e)}, 500
    
def fetch_all_units(staff_email):
    """
    Fetch all units for a specific staff.

    :param staff_email: The staff_email of the staff 
    :return: message for success or failure
    """
    try:
        # Step 1: Retrieve staff based on email
        staff = db.session.execute(select(Staff).filter_by(staff_email=staff_email)).scalar_one_or_none()

        if staff is None:
            return {"message": "Staff not found"}, 404

        # Step 2: Retrieve both convener and TA units
        convener_units = staff.units_convener
        ta_units = staff.units_ta

        staff_units_list = []

        # Step 3: Combine both convener and TA units into a single list
        for unit in convener_units + ta_units:
            staff_units_list.append({
                "unit_code": unit.unit_code,
                "unit_name": unit.unit_name,
                "year": unit.unit_year,
                "session": unit.unit_session,
                "level": unit.unit_level
            })

        # Step 4: Return the list of units
        return staff_units_list, 200

    except Exception as e:
        return {"message": "An error occurred while retrieving all the units.", "error": str(e)}, 500
