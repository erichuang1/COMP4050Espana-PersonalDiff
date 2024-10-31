from sqlalchemy import select
import csv
from flask import request

from src.db_instance import db
from src.models.models_all import *
import src.file_management as fm

def upload_student_csv(unit_code, request):
    """
    :param unit_code: The unit_code of the unit 
    :param files: The uploaded CSV file with student names and IDs
    :return: JSON object with details of the uploaded files or an error message.
    """
    # Use the file management to store the file
    status, file_path = fm.store_file_req(request)

    if status != fm.FileStatus.OKAY:
        return {"message": "File upload failed", "error": status.name}, 400

    # Extract the filename
    file = request.files['file']
    filename = fm.secure_filename(file.filename)

    # Save the file information in the database
    try:
        new_student_csv = StudentCSV(
            studentcsv_file_name=filename,
            studentcsv_file_path=file_path,
            unit_code=unit_code,
        )
        
        db.session.add(new_student_csv)
        db.session.commit()

        return {
            "message": "File uploaded and saved successfully",
            "file_name": new_student_csv.studentcsv_file_name,
            "file_path": new_student_csv.studentcsv_file_path
        }, 201

    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while saving the file information.", "error": str(e)}, 500

def fetch_students_list(unit_code):
    """
    :param unit_code:  The unit_code of the unit 
    :return: JSON object with details of the students
    """
    # Retrieve StudentCSV entries for the unit
    student_csv_files = db.session.execute(select(StudentCSV).filter_by(unit_code=unit_code)).scalars()

    if not student_csv_files:
        return {"message": "No student data found for this unit"}, 404

    # Create an empty list to store student data
    student_list = []

    # Iterate through each CSV file and extract student data
    for csv_file in student_csv_files:
        csv_path = csv_file.studentcsv_file_path
        
        # Use get_file method to retrieve the file
        file_status, file = fm.get_file(csv_path)
        
        # validate the file path and extension
        if file_status == fm.FileStatus.BAD_PATH:
            return {"message": f"File not found: {csv_path}"}, 404
        elif file_status == fm.FileStatus.BAD_EXTENSION:
            return {"message": f"Invalid file extension for file: {csv_path}"}, 400
        elif file_status == fm.FileStatus.OKAY:
            try:
                with file:
                    csv_reader = csv.DictReader(file)
                    for row in csv_reader:
                        student_list.append({
                            "student_id": row.get("student_id"),
                            "student_name": row.get("student_name"),
                        })
            except Exception as e:
                return {"message": f"Error reading file {csv_path}: {str(e)}"}, 400
        else:
            return {"message": "An unknown error occurred"}, 500

    if not student_list:
        return {"message": "No student records found in the CSV files"}, 404

    return {"students": student_list}, 200
