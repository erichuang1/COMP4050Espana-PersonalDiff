from io import StringIO
import time
from flask import json, send_file
# from src.file_management import *
from src.models.models_all import *
from src.db_instance import db
from sqlalchemy import select

import src.formatting as formatting
# from src.job_subsystem import SubsystemStatus
import src.job_subsystem as js
import src.file_management as fm

def create_rubric(data):
    '''
    Generate rubric based on the input received from the learning design staff member
    :param data: Contains everything expected from the learning design staff member for rubric generation
    :return: JSON object with details of the jobid and job status for that rubric
    :implementation details: 
        1. Send the `data` to the function in the job subsystem responsible for sending a rubric generation
            request to the AI module 
                - That function in the job subsystem should receive the generated rubric in JSON format from the AI module
                and save it as a json file in s3 (same as what is done for question generation)
        2. Receive 
    '''
    try: 
        # Extract the required details the AI module needs to receive for rubric generation 
        rubric_title = data.get('rubric_title')
        assessment_description = data.get('assessment_description')
        criteria = data.get('criteria')
        ulos = data.get('ulos')
        staff_email = data.get('staff_email')
        # Look up the staff using staff_email and see if they exist / have logged/signed into application before
        existing_staff = db.session.execute(select(Staff).filter_by(staff_email=staff_email)).scalar_one_or_none()
        if existing_staff is None:
            return{"message": f"Learning design staff member with email {staff_email} not found"}, 404
        # Send the `data` to the function in the job subsystem responsible for sending a rubric generation request to the AI module
        # job_status, job_id  = js.submit_new_rubric_job(staff_email, assessment_description, criteria, ulos)
        status, ulos_path = fm.create_json_file(rubric_title + "_ULOs.json", ulos)
        job_status, job_id  = js.submit_new_rubric_gen(assessment_description, staff_email, criteria, ulos_path)

        if job_status != js.SubsystemStatus.OKAY:
            return {"error": f"Failed to submit job for question generation checking status {job_status}"}, 500
        
        response_body = {
                "job_id": job_id,   
                "status": str(job_status)
        }
        
        return{"message" : "Rubric has been generated successfully",
                    "job" : response_body}, 200
    except Exception as e:
        return {"message": "An error occurred while generating this rubric.", "error": str(e)}, 500

def upload_generated_rubric(staff_email, rubric_title, generated_rubric_file_name, generated_rubric_file_path, status):
    '''
        Helper method to add the generated rubric details to the database.
        :param generated_rubric_file_name : name of the generated rubric file.
        :param generated_rubric_file_path : path of the generated rubric file.
        :status : status of the rubric eg. Rubric Generated
        :use : To be called by the job subsystem once the AI has returned the rubric generated in JSON format
                And the job subsystem has saved the rubric as a JSON file in S3 storage
                And returns the name, path and status of the rubric generated so that those details can be 
                saved in the database
    '''
    # Step 1: Get the staff_id using the staff_email from the staff table
    created_by_staff = db.session.execute(select(Staff).filter_by(staff_email=staff_email)).scalar_one_or_none()
    # Step 2: Create a new RubricGenerated record and add it to the database
    new_rubric = RubricGenerated(
        rubric_title = rubric_title,
        rubric_json_s3_file_name = generated_rubric_file_name,
        rubric_json_s3_file_path = generated_rubric_file_path,
        rubric_generation_status = status,
        created_by_learning_design_staff_id = created_by_staff.staff_id
    )
    db.session.add(new_rubric)
    
    # Step 3: Commit the transaction to the database
    try: 
        db.session.commit()
        return {
            "message": "Rubric generated successfully.",
        }, 201
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while saving generated rubric details to DB", "error": str(e)}, 500

def get_rubric(rubric_id):
    from src.job_subsystem import SubsystemStatus

    # Step 1: Retrieve rubric
    rubric = db.session.execute(select(RubricGenerated).filter_by(rubric_id=rubric_id)).scalar_one_or_none()

    # If the rubric does not exist, return an error message
    if rubric is None:
        return {"message": "Rubric not found"}, 404
    
    # Step 2: Retrieve the generated rubric file from the s3 path
    try: 
        rubric_file_path = rubric.rubric_json_s3_file_path
        # Use the get_file function to retrieve the file from s3
        status, file = fm.get_file(rubric_file_path)
        if status == fm.FileStatus.BAD_PATH:
            return {"message": f"File {rubric_file_path} not found in S3."}, 404
        elif status == fm.FileStatus.BAD_EXTENSION:
            return {"message": "File has an invalid extension."}, 400
        elif status == fm.FileStatus.UNKNOWN_ERR:
            return {"message": "An unknown error occurred while retrieving the file from S3."}, 500
        
        # Step 3: Load the outer JSON from the file-like object 
        rubric_json = json.load(file)
        # Step 4: Handle protential double encoding : to be done after confirming how things are stored in the file 
        # Iterate over all key-value pairs in the JSON and ecode if the value is a string
        # for key, value in rubric_json.items(): 
        #         if isinstance(value, str):
        #                 # Try decoding the string into a proper JSON object
        #                 rubric_json[key] = json.loads(value)
        #         else:
        #             continue
        # Return the full rubric JSON
        return rubric_json, 200
    except Exception as e:
        return {"message": f"An error occurred while retrieving the rubric/decoding JSON from the rubric file. Error: {str(e)}"}, 500

def update_rubric_changes(rubric_id, data):
    """
    Updates the JSON content for a given rubric JSON file in S3 and returns an appropriate status
    based on the user's changes made to the rubric.
    :param rubric_id: The ID of the rubric to update.
    :param data: The new JSON data to replace the existing rubric.
    :return: A tuple of response data (status message) and status code.
    """
    try:
        # Step 1: Retrieve the rubric from the database
        rubric = db.session.execute(select(RubricGenerated).filter_by(rubric_id=rubric_id)).scalar_one_or_none()

        if rubric is None:
            return {"message": "Rubric not found."}, 404

        # Step 2: Update the JSON data in S3
        rubric_file_path = rubric.rubric_json_s3_file_path
        status, _ = fm.get_file(rubric_file_path)  # Check if the file exists in S3

        if status == fm.FileStatus.BAD_PATH:
            return {"message": "Rubric file not found in S3."}, 404
        elif status != fm.FileStatus.OKAY:
            return {"message": "An unknown error occurred while retrieving the rubric file."}, 500

        # Step 3: Replace the existing JSON in S3 with the new data
        status, message = fm.update_file_in_s3(rubric_file_path, json.dumps(data), 'application/json')

        if status != FileStatus.OKAY:
            return {"message": f"Failed to update rubric in S3: {message}"}, 500
        # Step 4: Retrieve the updated rubric file from the s3 path
        rubric_file_path = rubric.rubric_json_s3_file_path
        # Use the get_file function to retrieve the file from s3
        status, file = fm.get_file(rubric_file_path)
        if status == fm.FileStatus.BAD_PATH:
            return {"message": f"File {rubric_file_path} not found in S3."}, 404
        elif status == fm.FileStatus.BAD_EXTENSION:
            return {"message": "File has an invalid extension."}, 400
        elif status == fm.FileStatus.UNKNOWN_ERR:
            return {"message": "An unknown error occurred while retrieving the file from S3."}, 500
        
        # Step 5: Load the outer JSON from the file-like object 
        rubric_json = json.load(file)
        return {"message": "Rubric updated successfully",
                "updated_rubric_json": rubric_json}, 200

    except Exception as e:
        return {"message": f"An error occurred while updating the rubric {rubric_id}.", "error": str(e)}, 500

def delete_rubric_from_db(rubric_id):
        # Retrieve rubric
        rubric = db.session.execute(select(RubricGenerated).filter_by(rubric_id=rubric_id)).scalar_one_or_none()
        # If the rubric does not exist, return an error message
        if rubric is None:
            return {"message": "Rubric not found"}, 404
        filestatus = fm.del_file(rubric.rubric_json_s3_file_name)
        if filestatus != FileStatus.OKAY:
            return {"message": f"File `{rubric.rubric_json_s3_file_name}` could not be deleted", "error": filestatus.name}, 400
        else:
            db.session.delete(rubric)
        try:
            db.session.commit()
            return {"message" : f"File {rubric.rubric_json_s3_file_name} was deleted successfully"}, 200
        except Exception as e:
            db.session.rollback()
            return {"message": "An error occurred while deleting rubric file", "error": str(e)}, 500 

def fetch_all_rubrics(staff_email):
    try:
        # Step 1: Retrieve staff based on email
        staff = db.session.execute(select(Staff).filter_by(staff_email=staff_email)).scalar_one_or_none()

        #Step 2: Check if the staff exists
        if staff is None:
            return {"message": "Staff not found"}, 404

        # Step 3: Retrieve all the rubric list
        rubrics = db.session.execute(select(RubricGenerated).filter_by(created_by_learning_design_staff_id=staff.staff_id)).scalars()

        #Step 4:  Create an empty rubrics list, add each rubric
        rubrics_list = []
        for rubric in rubrics: 
            rubrics_list.append({
                    "rubric_id": rubric.rubric_id,
                    "rubric_title": rubric.rubric_title,
                    "rubric_json_s3_file_name": rubric.rubric_json_s3_file_name,
                    "rubric_generation_status": rubric.rubric_generation_status,
                    "created_by": staff.staff_name
                })
        return {"rubrics": rubrics_list}, 200
    except Exception as e:
        return {"message": "An error occurred while retrieving all the rubrics.", "error": str(e)}, 500 

def get_job_status(job_id):
    try:
        # Query the job status from the JobSubsystem
        job_status = js.get_job_status(job_id)  

        # Check if current job status
        if job_status == js.SubsystemStatus.COMPLETED_JOB:
            return {
                "message": "Rubric generation is completed.",
                "job_id": job_id,
                "status": "COMPLETED", 
            }, 200
        elif job_status == js.SubsystemStatus.AWAITING_INSTANCE:
            return {
                "message": "Rubric generation is in progress.",
                "job_id": job_id, 
                "status": "IN_PROGRESS"
            }, 200
        else:
            return {
                "message": "Rubric generation failed.",
                "job_id": job_id, 
                "status": "FAILED"
            }, 200
    except Exception as e :
            return {"message": "An error occurred while getting the status for {rubric_id}.", "error": str(e)}, 500

def download_rubric_as(rubric_id, format):
    rubric = db.session.execute(select(RubricGenerated).filter_by(rubric_id=rubric_id)).scalar_one_or_none()
    
    if rubric is None:
        return {"message": "Rubric not found"}, 404
    
    status,rubric_str = fm.get_file(rubric.rubric_json_s3_file_path)
    rubric_dict = json.load(rubric_str)
    rubric_md_text = formatting.rubric_make_md(rubric_dict)

    match format.lower():
        case "md":
            download_file = StringIO(rubric_md_text)
            download_file.seek(0)
            download_name = "rubric.md"
            mimetype = 'text/markdown'
        case "pdf":
            status,download_file = fm.convert_md_str_to_pdf_bytes(rubric_md_text, None)
            download_name = "rubric.pdf"
            mimetype = 'application/pdf'
        case "xls":
            status,download_file = formatting.rubric_make_xls_data(rubric_dict)
            download_file.seek(0)
            download_name = "rubric.xls"
            # mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            mimetype = 'application/vnd.ms-excel'
        case _:
            return {"message": "Unsupported format"}, 400

    try:
        return send_file(download_file, as_attachment=True, download_name=download_name, mimetype=mimetype)
    except Exception as e:
        return {"message": f"An error occurred while downloading the generated rubric {rubric_id}", "error": str(e)}, 500
    
    