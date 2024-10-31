import csv
from src.db_instance import db
from src.models.models_all import *
from src.file_management import *
from sqlalchemy import select

def add_questions(unit_code, project_title, request):
    """
    Upload questions to the question bank for a specific project.
    :param unit_code: The unit_code of the unit 
    :param project_title: name of the project to add the questink bank
    :param data: The data containing the questions.
    :return: JSON object with a success message or an error message.
    """
    # Step 1: Use the file management to store the file
    status, file_path = store_file_req(request)

    # Step 2: Check the STATUS
    if status != FileStatus.OKAY:
        return {"message": "File upload failed", "error": status.name}, 400

    # Step 3: Extract the filename
    file = request.files['file']
    filename = secure_filename(file.filename)

    project = db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_title)).scalar_one_or_none()
    # If project does not exist, return error message
    if project is None:
        return {"message": f"Project not found in unit {unit_code}."}, 404
    # Step 4: Save info to database
    new_question_bank = QnBank(
        qnbank_file_name=filename,
        qnbank_file_path=file_path,
        project_id=project.project_id,
        unit_code=unit_code,
    )

    try :
        # Add to the database session and commit
        db.session.add(new_question_bank)
        db.session.commit()
        return {
            "message": "File uploaded to QuestionBank successfully.",
            "question_bank": {
                "qnbank_file_name": filename,
                "qnbank_file_path": file_path,
                "project_id": project.project_id,
                "unit_code": unit_code,
            }
        }, 201
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while saving the file information.", "error": str(e)}, 500
    
def retrieve_questions_from_db(unit_code, project_title):
    """
    Retrieve all questions from the question bank for a specific project
    :param unit_code: The unit_code of the unit 
    :param project_title: name of the project to add the questink bank
    :return: JSON object with the list of questions or an error message.
    """
    # Step 1: Retrieve Question files list from QuestionBanl for the project
    project = db.session.execute(select(Project).filter_by(unit_code=unit_code,project_name=project_title)).scalar_one_or_none()

    # If project does not exist, return error message
    if project is None:
        return {"message": f"Project not found in unit {unit_code}."}, 404


    question_bank_files = db.session.execute(select(QnBank).filter_by(unit_code=unit_code, project_id=project.project_id)).scalars().all()
    # Step 2: Check if any files rae there
    if not question_bank_files:
        return {"message": "No quetsion files found for this project"}, 404
    latest_question_bank = question_bank_files[-1] if question_bank_files else None
    
    # Create an empty list to store questions data
    question_list = []

    # Iterate through each CSV file and extract questions data
    # for csv_file in question_bank_files:
    csv_path = latest_question_bank.qnbank_file_path
    
    # Use get_file method to retrieve the file
    file_status, file = get_file(csv_path)
    
    # validate the file path and extension
    if file_status == FileStatus.BAD_PATH:
        return {"message": f"File not found: {csv_path}"}, 404
    elif file_status == FileStatus.BAD_EXTENSION:
        return {"message": f"Invalid file extension for file: {csv_path}"}, 400
    elif file_status == FileStatus.OKAY:
        try:
            with file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    question_list.append(row)
        except Exception as e:
            return {"message": f"Error reading file {csv_path}: {str(e)}"}, 400
    else:
        return {"message": "An unknown error occurred"}, 500

    if not question_list:
        return {"message": "No questions found in the Question Bank files"}, 404

    return {"questions": question_list}, 200

def delete_qn_bank_from_db(unit_code, project_title):
    """
        Delete the question banks from the project
    """
    # Step 1: Retrieve the Project from the db
    project = db.session.execute(select(Project).filter_by(unit_code=unit_code,project_name=project_title)).scalar_one_or_none()
    # If project does not exist, return error message
    if project is None:
        return {"message": f"Project not found in unit {unit_code}."}, 404
    # Step 1: Retrieve the Question Banks for that project from the db
    question_banks_to_delete = db.session.execute(select(QnBank).filter_by(project=project)).scalars()
    for question_bank_to_delete in question_banks_to_delete:
        db.session.delete(question_bank_to_delete)
    try:
        db.session.commit()
        return {"message" : f"All qn banks in this  was deleted successfully"}, 200
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while deleting question banks", "error": str(e)}, 500 