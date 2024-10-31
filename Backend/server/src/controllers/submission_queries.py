from sqlalchemy import select
from sqlalchemy import text

from src.db_instance import db
from src.models.models_all import *
import src.file_management as fm

def batch_upload_pdfs(unit_code, project_title, staff_email, files):
    """
    Upload multiple pdfs submissions for a specific project within a unit.

    :param unit_code: The code of the unit.
    :param project_title: The title of the project.
    :param files: The uploaded PDF files.
    :return: JSON object with details of the uploaded files or an error message.
    """
    # Step 1: Retrieve the project for which submission is done
    project = db.session.execute(select(Project).filter_by(unit_code = unit_code, project_name = project_title)).scalar_one_or_none()

    if project is None:
        return {"message": "Project not found"}, 404
    
    # create am empty list to store submission details
    uploaded_files = []
    # Step 2: Loop through each file
    for file in files:
        # Step 2.1: Validate file extension
        if not fm._allowed_filename(file.filename):
            return {"message": f"File {file.filename} has an invalid extension"}, 400
        
        # Step 2.2: Upload the file using file management
        file_status, file_path = fm.store_file_storage(file)
        if file_status != fm.FileStatus.OKAY:
            return {"message": f"File {file.filename} upload failed", "error": file_status.name}, 400
    
        # Step 3: Get the staff details of the uploader using the staff_email
        staff = db.session.execute(select(Staff).filter_by(staff_email = staff_email)).scalar_one_or_none()
        # Step 4: Store the file details in the database (Submission table)
        new_submission = Submission(
            submission_file_name = file.filename,
            submission_file_path = file_path,
            submission_status = "Uploaded", 
            uploader_id = staff.staff_id,
            project_id = project.project_id,
            unit_code = unit_code,
        )
        
        db.session.add(new_submission)
        try:
            # Step 4: Commit the transaction to the database
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"message": "An error occurred while saving submission data", "error": str(e)}, 500
        # Add file details to the response list
        uploaded_files.append({
            "submission_id": new_submission.submission_id,
            "submission_file_name": new_submission.submission_file_name,
            "submission_status": new_submission.submission_status
        })
        
    return {
            "message": "Files successfully uploaded",
            "uploaded_files": uploaded_files
        }, 201


def get_list_of_submission_files(unit_code, project_title):

    """
    Retrieve all submission file details (not the actual files) related to a specific project within a unit.

    :param unit_code: The code of the unit.
    :param project_title: The title of the project.
    :return: JSON object with a details of the submission files (list)
    """
    project = db.session.execute(select(Project).filter_by(unit_code = unit_code, project_name = project_title)).scalar_one_or_none()
    if project is None:
        return {"message": "Project not found"}, 404
    
    # Raw SQL query : https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.text

    sql = text("SELECT submission_id, submission_file_name, submission_status FROM submission WHERE project_id = :project_id AND unit_code = :unit_code")
    
    # Execute raw SQL query
    result = db.session.execute(sql, {'project_id': project.project_id, 'unit_code': project.unit_code})
    
    # Fetch all results
    submissions = result
    if not submissions:
        return{
            "message": "This project does not have any submissions"
        }, 404
    
    submission_files = []
    for submission in submissions:
        submission_files.append({
            "submission_id": submission.submission_id,
            "submission_file_name": submission.submission_file_name,
            "submission_status":submission.submission_status
        })
    try: 
        return{
            "message": "Retrieved list of submission files successfully",
            "submission_files": submission_files
    
        }, 200
    except Exception as e:
        return {"message" : "An error occured while retrieiving the list of submissions for this prpject",
                "error" : str(e)}, 500
     
# User wants to delete all the submissions for a specific project in a unit
def delete_all_files(unit_code, project_title):
    """
    Delete all files(submission files) related to a specific project within a unit.

    :param unit_code: The code of the unit.
    :param project_title: The title of the project.
    :return: Message indicating success or failure.
    """
    try:
        # Step 1: Retrieve the project for which submission is done
        project = db.session.execute(select(Project).filter_by(unit_code = unit_code, project_name = project_title)).scalar_one_or_none()

        if project is None:
            return {"message": "Project not found"}, 404
        
        # Step 2: Retrieve all submissions related to the project
        submissions = db.session.execute(select(Submission).filter_by(unit_code = unit_code, project_id = project.project_id)).scalar_one_or_none()

        if submissions is None:
            return {"message": "No Submissions found"}, 404
        # Step 3: Go through each submission in the project and interface with the File System to delete it 
        for submission in submissions:
            filestatus = fm.del_file(submission.submission_file_name)
            if filestatus != fm.FileStatus.OKAY:
                return {"message": f"File {submission.submission_file_name} could not be deleted", "error": filestatus.name}, 400
            else:
                db.session.delete(submission)
                return {"message" : f"File {submission.submission_file_name} was deleted successfully"}, 200
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred deleting submission files", "error": str(e)}, 500
 
def delete_file_from_db(unit_code, project_title, submission_id):
    """
    Delete single file(submission file) related to a specific project within a unit.

    :param unit_code: The code of the unit.
    :param project_title: The title of the project.
    :return: Message indicating success or failure.
    """
    submission = db.session.execute(select(Submission).filter_by(submission_id = submission_id)).scalar_one_or_none()
    if submission is None:
        return {"message": f"Submission with ID {submission_id} not found"}, 404
    
    filestatus = fm.del_file(submission.submission_file_name)
    if filestatus != fm.FileStatus.OKAY:
        return {"message": f"File {submission.submission_file_name} could not be deleted", "error": filestatus.name}, 400
    else:
        db.session.delete(submission)
    try:
        db.session.commit()
        return {"message" : f"File {submission.submission_file_name} was deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while deleting submission file", "error": str(e)}, 500 

