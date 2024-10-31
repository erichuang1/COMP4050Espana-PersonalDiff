from flask import json, send_file
from sqlalchemy import select
from src.db_instance import db
from src.models.models_all import *

from src.file_management import _allowed_filename, store_file_storage, del_file, FileStatus
from src.job_subsystem import SubsystemStatus, submit_new_rubric_convert

def upload_marking_guide_to_db(staff_email, file):
    '''
        Upload file(marking guide)
        :param staff_email: The email of the staff who uploaded the marking guide
        :param file: The pdf file for marking guide
        :return: Message indicating success or failure.
    '''
    try:
        # Step 0: Get the staff who created the marking_guide and check if that staff exists
        staff = db.session.execute(select(Staff).filter_by(staff_email=staff_email)).scalar_one_or_none()
        if staff is None: 
            return {"message": "Staff email not found"}, 404
        # Step 1: Validate the file type 
        if not _allowed_filename(file.filename):
            return {"message": f"File {file.filename} has an invalid extension"}, 400
        
        # Step 2: Store the file in a file storage system 
        file_status, file_path = store_file_storage(file)
        
        if file_status != FileStatus.OKAY:
            return {"message": "File upload failed.", "error": file_status.name}, 400

        # Step 3: Store the file details in the database (Marking Guide table)
        new_marking_guide = MarkingGuide(
            marking_guide_file_name=file.filename,
            marking_guide_s3_file_path=file_path,
            marking_guide_conversion_status="Uploaded",
            uploaded_by_learning_design_staff_id = staff.staff_id
        )

        db.session.add(new_marking_guide)
        db.session.commit()
        return {"message": "Marking Guide uploaded successfully.", 
                "marking_guide_details": 
                    {
                        "marking_guide_id": new_marking_guide.marking_guide_id,
                        "file_name": new_marking_guide.marking_guide_file_name,
                        "status": new_marking_guide.marking_guide_conversion_status,
                   }
                }, 201
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while uploading the marking guide.", "error": str(e)}, 500


def generate_marking_guide_rubric(marking_guide_id, data):
    '''
        Convert the selected marking guide to rubric 
        :param marking_guide_id: ID of the selected marking guide
        :return: Message indicating success or failure.
  
    '''
    try:
        # Step 1: Retrive the marking guide from db
        marking_guide = db.session.execute(select(MarkingGuide).filter_by(marking_guide_id = marking_guide_id)).scalar_one_or_none()

        # Step 2: Check if marking guide exists
        if marking_guide is None :
            return {"message" : "Marking guide not found."}, 404
        
        #Step 3: Extarct the data 
        staff_email = data.get('staff_email')
        ulos = data.get('ulos')
        # Check if 'ulos' is a list and has at least one item
        if not isinstance(ulos, list) or len(ulos) == 0:
            return {"message": "The 'ulos' field must be a non-empty list."}, 400
        # Step 4: TODO Send request to job subsystem 
        job_status, job_id  = submit_new_rubric_convert(marking_guide.marking_guide_s3_file_path, staff_email, ulos, marking_guide_id)

        if job_status != SubsystemStatus.OKAY:
            return {"error": f"Failed to submit job for question generation checking status {job_status}"}, 500
        
        response_body = {
            "job_id": job_id,   
            "status": str(job_status)
        }
            
        return{"message" : "Rubric has been generated successfully",
               "job" : response_body}, 200
    except Exception as e:
        return {"message": "An error occurred while generating this rubric.", "error": str(e)}, 500


def upload_generated_rubric_from_mg(staff_email, rubric_title, generated_rubric_file_name, generated_rubric_file_path, status, marking_guide_id):
    '''
        Helper method to add the generated rubric details to the database.
        :param generated_rubric_file_name : name of the generated rubric file.
        :param generated_rubric_file_path : path of the generated rubric file.
        :status : status of the rubric eg. Rubric Generated
        :marking_guide_id: id of the marking guide that was used to generate the rubric
        :use : To be called by the job subsystem once the AI has returned the rubric generated in JSON format
                And the job subsystem has saved the rubric as a JSON file in S3 storage
                And returns the name, path and status of the rubric generated so that those details can be 
                saved in the database
    '''
    # Step 1: Get the staff_id using the staff_email from the staff table
    created_by_staff = db.session.execute(select(Staff).filter_by(staff_email=staff_email)).scalar_one_or_none()
    
    # Step 2: Get the marking guide that was used to generate the rubric
    marking_guide_used = db.session.execute(select(MarkingGuide).filter_by(marking_guide_id=marking_guide_id)).scalar_one_or_none()
    # Step 3: Save rubric generated to db
    new_rubric = RubricGenerated(
        rubric_title = rubric_title,
        rubric_json_s3_file_name = generated_rubric_file_name,
        rubric_json_s3_file_path = generated_rubric_file_path,
        rubric_generation_status = status,
        created_by_learning_design_staff_id = created_by_staff.staff_id
    )
    db.session.add(new_rubric)
    
    # Step 4: Commit the transaction to the database
    try: 
        db.session.commit()
        marking_guide_used.rubric_generated_from_mg = new_rubric.rubric_id
        return {
            "message": "Rubric generated successfully.",
        }, 201
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while saving generated rubric details to DB", "error": str(e)}, 500







