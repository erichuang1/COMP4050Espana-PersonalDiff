from sqlalchemy import select

from src.db_instance import db
from src.models.models_all import *

def add_collaborator_to_unit(unit_code, data):
    """
    Add an existing staff member/TA (already signed up) as a collaborator to a specific unit.

    :param unit_code: The code of the unit.
    :param data: The collaborator details (staff_id, role).
    :return: JSON object with details of the added collaborator or an error message.

    """
    # Using te latest version instead of legacy version
    # https://docs.sqlalchemy.org/en/20/tutorial/orm_data_manipulation.html#inserting-rows-using-the-orm-unit-of-work-pattern
    # 1. check if a unit with the unit_code passed in alraedy exists in the db
    unit = db.session.execute(select(Unit).filter_by(unit_code=unit_code)).scalar_one_or_none()
    if unit is None:
        return {"message": "Unit not found"}, 404
 
    # 2. Extract staff member/TA details from the data
    staff_id = data.get('staff_id')
    staff_name = data.get('staff_name') 
    role = data.get('role')
    
    if not staff_id or not role:
        return {"message": "Both staff_id and role are required"}, 400
    
    # 3. Check if staff member/TA has signed up to this application using Microsoft login
    existing_staff = db.session.execute(select(Staff).filter_by(staff_id=staff_id)).scalar_one_or_none()
    if existing_staff is None:
        return {"message": "This staff member has not signed up with this application yet"}, 404
                
    # 4. Check if that staff member is already a collaborator of the unit, with the requested role
    staff_member_unit_association = db.session.execute(select(ta_added_to_unit)
        .filter_by(staff_id=staff_id, unit_code=unit_code, ta_role_in_unit=role)).scalar_one_or_none()
    
    if staff_member_unit_association is not None:
        return {"message": "This staff member is already a collaborated of this unit with the exact same role"}, 404
    
    # 5. Allocate that TA/Staff member as a collaborator with the specified role to the specified unit 
        # https://docs.sqlalchemy.org/en/14/core/selectable.html#sqlalchemy.sql.expression.TableClause.insert
    db.session.execute(ta_added_to_unit.insert().values(
        staff_id = staff_id,
        unit_code = unit_code, 
        ta_role_in_unit = role
    ))
    
    try:
        db.session.commit()
        return {"message": "Staff member added successfully as a collaborator", "staff_member": {
            "name": existing_staff.staff_name,
            "role": role,
            "type": existing_staff.staff_type
        }}, 201
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while adding the collaborator", "error": str(e)}, 500

def update_collaborator_role(unit_code, data):
    """
    Update the role of a collaborator in a specific unit.

    :param unit_code: The code of the unit to which the TA is assigned
    :param data: Dictionary containing the staff_id and the updated role
    :return: JSON object with a success message or an error message
    """
    # Extract the staff ID and the new role from the data
    staff_id = data.get('staff_id')
    staff_name = data.get('staff_name')
    new_role = data.get('role')

    if not staff_id or not new_role:
        return {"message": "Both staff_id and role are required"}, 400

    existing_member_in_unit  = db.session.execute(select(ta_added_to_unit)
        .filter_by(staff_id=staff_id, unit_code=unit_code)).scalar_one_or_none()
    
    if existing_member_in_unit is None: 
        return {"message": "Teaching Assistant not found for this unit"}, 404
    
    # Update the role for the specific staff member in the unit
    # https://docs.sqlalchemy.org/en/14/core/dml.html#sqlalchemy.sql.expression.update
    db.session.execute(
        ta_added_to_unit.update()
        .where(
            (ta_added_to_unit.c.staff_id == staff_id) & 
            (ta_added_to_unit.c.unit_code == unit_code)
        )
        .values(ta_role_in_unit=new_role)
    )
    
    # Getting the details (name, role, type) of the staff member whose role was altered for that unit
    staff = db.session.execute(select(Staff)
        .filter_by(staff_id=staff_id)).scalar_one_or_none()
    try:
        db.session.commit()
        return {"message": "Staff member's role successfully changed/updated", "staff_member": {
            "name": staff.staff_name,
            "role": new_role,
            "type": staff.staff_type
        }}, 201
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while updating the collaborator role", "error": str(e)}, 500
    
def get_collaborators_for_unit(unit_code):
    """
        Retrieve all collaborators (staff members) assigned to a specific unit.

        :param unit_code: The code of the unit.
        :return: JSON object with a list of collaborators or an error message.
    """

    try: 
        # Step 1: Retrieve the Unit
        unit = db.session.execute(select(Unit).filter_by(unit_code=unit_code)).scalar_one_or_none()

        # If unit does not exist, return error message
        if unit is None:
            return {"message": "Unit not found."}, 404

        # Step 2: Retrieve all collaborators (staff members) for the unit
        collaborators = unit.teachingassistants
        if not collaborators:
             return {"message": f"No collaborators found for the unit {unit_code},"}, 404
        
        # Step 3: Add the collaborator data into a list
        collaborator_list = []
        for collaborator in collaborators:
            staff = db.session.execute(select(Staff).filter_by(staff_id=collaborator.staff_id)).scalar_one_or_none()
            if staff:
                collaborator_list.append({
                    "staff_id": staff.staff_id,
                    "staff_name": staff.staff_name,
                    "staff_email": staff.staff_email,
                    # "role": collaborator.ta_role_in_unit,
                    "type": staff.staff_type,
            })
        return {"unit_code": unit_code, "collaborators": collaborator_list}, 200
    except Exception as e: 
        return {"message": "An error occurred while retrieving the collaborators for the unit.", "error": str(e)}, 500


def get_non_collaborators_for_unit(unit_code):
    """
    Retrieve (staff members) that are NOT part of a unit.

    :param unit_code: The code of the unit.
    :return: JSON object with a list of non-collaborators or an error message.
    """

    try: 
        # Step 1: Retrieve the Unit
        unit = db.session.execute(select(Unit).filter_by(unit_code=unit_code)).scalar_one_or_none()

        # If unit does not exist, return error message
        if unit is None:
            return {"message": "Unit not found."}, 404

        # Step 2: Retrieve all collaborators (staff members) for the unit
        collaborators = unit.teachingassistants
        collaborator_ids = [collaborator.staff_id for collaborator in collaborators]

        # Add the convener's staff_id to the exclusion list
        if unit.unit_convener:
            collaborator_ids.append(unit.unit_convener.staff_id)

        # Step 3: Retrieve all staff who are NOT collaborators or the convener in the unit
        non_collab_staff = db.session.execute(
            select(Staff).filter(~Staff.staff_id.in_(collaborator_ids))
        ).scalars().all()

        # Step 4: Prepare the list of non-collaborators
        non_collaborator_list = [
            {
                "staff_id": staff.staff_id,
                "staff_name": staff.staff_name,
                "staff_email": staff.staff_email,
                "type": staff.staff_type,
            }
            for staff in non_collab_staff
        ]

        return {"unit_code": unit_code, "non_collaborators": non_collaborator_list}, 200

    except Exception as e: 
        return {"message": "An error occurred while retrieving the non-collaborators for the unit.", "error": str(e)}, 500


def get_all_staff():
    '''
        Retrive list of all staff
        return: JSON 
    ''' 
    try:
        all_staff = db.session.execute(select(Staff)).scalars()
        if not all_staff:
            return {"message": f"No staff found."}, 404
        
        staff_list = []
        for staff in all_staff :
            staff_list.append({
                "staff_id": staff.staff_id, 
                "staff_email": staff.staff_email,
                "staff_name": staff.staff_name, 
                "staff_type": staff.staff_type
                })

        return {"staffs": staff_list}, 200
    except Exception as e: 
        return {"message": "An error occurred while retrieving the all collaborators.", "error": str(e)}, 500

def delete_collaborator_for_unit(unit_code, staff_id):
    '''
        Delete collaborator
        :param unit_code: The unit code of the unit.
        :param staff_id: The staff ID of the staff member to be deleted
        return : message indicationg success or failure
    '''
    try:
        # Strp 1: Check if the unit exists
        unit = db.session.execute(select(Unit).filter_by(unit_code=unit_code)).scalar_one_or_none()
        if unit is None:
            return {"message": "Unit not found."}, 404
        
        # Step 2 : Retrive the Staff 
        existing_member_in_unit  = db.session.execute(select(ta_added_to_unit)
        .filter_by(staff_id=staff_id, unit_code=unit_code)).scalar_one_or_none()
    
        if existing_member_in_unit is None: 
            return {"message": "Teaching Assistant not found for this unit"}, 404
        

        # Step 3: Delete the specific staff member in the unit
        # https://docs.sqlalchemy.org/en/14/core/dml.html#sqlalchemy.sql.expression.update
        db.session.execute(
            ta_added_to_unit.delete()
            .where(
                (ta_added_to_unit.c.staff_id == staff_id) & 
                (ta_added_to_unit.c.unit_code == unit_code)
            )
        )
        db.session.commit()
        return {"message": "Collaborator deleted successfully."}, 200
    except Exception as e: 
        db.session.rollback()
        return {"message": "An error occurred while deleting the collaborators for the unit.", "error": str(e)}, 500
