from flask import jsonify, send_file
from src.db_instance import db
from src.models.models_all import *
from sqlalchemy import select, text
from src.file_management import *
from src.job_subsystem import submit_new_viva_gen, submit_new_viva_regen, SubsystemStatus
import traceback

def generate_for_all(unit_code, project_title):
    '''
     Generate questions for all submission file for a specific project within a unit.
    :param unit_code: The unit_code of the unit 
    :param project_title: The title of the project.
    :return: JSON object with details of the jobid and job status.
    '''
    try:
        # Step 1 : Retrive the project
        project = db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_title)).scalar_one_or_none()
        unit = db.session.execute(select(Unit).filter_by(unit_code=unit_code)).scalar_one_or_none()
        if unit is None:
            return {f"message": "Unit not found."}, 400

        if project is None:
            return {"message": f"Project not found exists in unit {unit_code}."}, 400

        # Step 2: Extract the details related to question generation template from project db
        factual_recall_count = project.factual_recall_count
        conceptual_understanding_count = project.conceptual_understanding_count
        analysis_evaluation_count = project.analysis_evaluation_count
        application_problem_solving_count = project.application_problem_solving_count
        open_ended_discussion_count = project.open_ended_discussion_count
        challengeLevel = project.questions_difficulty
  
        # Step 3:  Fetch all results
        submissions = project.all_submissions
        if not submissions:
            return{
                "message": "This project does not have any submissions"
            }, 404

        jobs = []

        #Step 4 : Send Each submission to _submit_new_job( sub_id, qns_count, unit code, level )
        for submission in submissions:
            job_status, message, job_id = submit_new_viva_gen(submission.submission_id, submission.submission_file_path,
                                            project.project_name, unit.unit_name, unit.unit_level, challengeLevel, 
                                            factual_recall_count, analysis_evaluation_count, open_ended_discussion_count, 
                                            application_problem_solving_count, conceptual_understanding_count )
            if job_status != SubsystemStatus.OKAY:            
                return {"error": f"Failed to submit job for question generation checking status {job_status}, JobID: {job_id}, message :{str(message)}"}, 500

            jobs.append({
                    "submission_id": submission.submission_id,
                    "job_id": job_id,
                    "status": str(job_status)
            })
        return{"message" : "Submission files have been sent for Question Generation.",
                    "jobs" : jobs}, 200
    except Exception as e:
            return {"message": f"An error occurred while generating questions.", "error": str(e)}, 500

def generate_for_submission(unit_code, project_title, submission_id):
    '''
    Generate questions for a specific submission
    :param unit_code: The unit_code of the unit 
    :param project_title: The title of the project.
    :param submission_id: The ID of the submission
    :return: JSON object with details of the jobid and job status.
    '''
    # Step 1 : Retrive the project
    project = db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_title)).scalar_one_or_none()
    unit = db.session.execute(select(Unit).filter_by(unit_code=unit_code)).scalar_one_or_none()
    if unit is None:
        return {"message": "Unit not found."}, 400
    if project is None:
        return {"message": f"Project not found in unit {unit_code}."}, 400

    # Step 2: Extract the details related to question generation template from project db
    factual_recall_count = project.factual_recall_count
    conceptual_understanding_count = project.conceptual_understanding_count
    analysis_evaluation_count = project.analysis_evaluation_count
    application_problem_solving_count = project.application_problem_solving_count
    open_ended_discussion_count = project.open_ended_discussion_count
    challengeLevel = project.questions_difficulty

    # Step 3: Retrieve submission
    submission = db.session.execute(select(Submission).filter_by(submission_id = submission_id)).scalar_one_or_none()
    
    # Step 4 : Send the submission to _submit_new_job( sub_id, qns_count, unit code, level )
    job_status, message, job_id = submit_new_viva_gen(submission.submission_id, submission.submission_file_path,
                                            project.project_name, unit.unit_name, unit.unit_level, challengeLevel, 
                                            factual_recall_count, analysis_evaluation_count, open_ended_discussion_count, 
                                            application_problem_solving_count, conceptual_understanding_count )
    # Step 5 : Check the job status
    if job_status != SubsystemStatus.OKAY:            
        return {"error": f"Failed to submit job for question generation checking status {job_status}, JobID: {job_id}, message :{str(message)}"}, 500

    try:
        return{
            "message": f"Submission file  {submission_id} has been sent for Question Generation",
            "job_status": str(job_status),
            "job_id": job_id}, 200
    except Exception as e:
            return {"message": f"An error occurred while generating questions for submission ID {submission_id}.", "error": str(e)}, 500

def upload_generated_files(submission_id, generated_file_name, generated_file_path, status ):
        '''
            Helper method to add the generated questions details to the database.
            :param submission_id: The ID of the submission.
            :param generated_file_name : name of the generated questions file.
            :param generated_file_path : path of the generated questions file.
            :status : status of the submission eg. Questions generated
        '''
        # Step 1 : Create a new GeneratedQnFile record and add it to the database
        new_generated_file = GeneratedQnFile(
            generated_qn_file_name = generated_file_name,
            generated_qn_file_path = generated_file_path,
            submission_id = submission_id
        )

        # Step 2 : Add the question generated file to the Database
        db.session.add(new_generated_file)

        submission = db.session.execute(select(Submission).filter_by(submission_id = submission_id)).scalar_one_or_none()
        submission.submission_status = status
        generated_files = []

        generated_files.append({
            "submission_id": submission_id,
            "question_file_name": new_generated_file.generated_qn_file_name
        })

        # Step 3: Commit the transaction to the database
        try:
            db.session.commit()
            return {
                "message": "Questions are successfully generated for all Submssions.",
            }, 201
        except Exception as e:
            db.session.rollback()
            return {"message": "An error occurred while saving generated data to DB", "error": str(e)}, 500
    
def regenerate_questions(unit_code, project_title, submission_id, data):
    '''
    Re-Generate questions for a specific submission
    :param unit_code: The unit_code of the unit 
    :param project_title: The title of the project.
    :param submission_id: The ID of the submission
    :return: JSON object with details of the jobid and job status.
    '''
    # Step 1 : Retrive the project
    project = db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_title)).scalar_one_or_none()
    unit = db.session.execute(select(Unit).filter_by(unit_code=unit_code)).scalar_one_or_none()
    
    if project is None:
        return {f"message": "Project not found in unit {unit_code}."}, 400

    # Step 2: Retrieve submission
    submission = db.session.execute(select(Submission).filter_by(submission_id = submission_id)).scalar_one_or_none()
    
    if submission is None:
        return {"message": f"Submission with ID {submission_id} not found."}, 404

    question_reason_list = data.get("question_reason")

    # Step 3: Retrieve the generated question file details from the database
    question_files_generated = db.session.execute(
        select(GeneratedQnFile).filter_by(submission_id=submission_id)).scalars().all()

    # Step 4 : Send the submission to _submit_new_job( sub_id, qns_count, unit code, level ) 
    job_status, message, job_id = submit_new_viva_regen(submission.submission_id, submission.submission_file_path, project.project_name,
                                                        unit.unit_name, question_reason_list, question_files_generated[-1].generated_qn_file_path)
    
    # Step 5 : Check the job status
    if job_status != SubsystemStatus.OKAY:            
        return {"error": f"Failed to submit job for question generation checking status {job_status}, JobID: {job_id}, message :{str(message)}"}, 500

    try:
        return{
        "submission_id": submission_id,
        "message": "Submission file has been sent for Question Re-Generation",
        "job_status": str(job_status),
        "job_id": job_id}, 200
    except Exception as e:
        return {"message":f"An error occurred while regenerating questions for submission {submission_id}.", "error": str(e)}, 500

def get_questions_for_submission(submission_id):
    '''
    Retrieve the generated questions (static, random, AI-generated) for a specific submission.
    Handles double-encoded JSON if needed.
    
    :param submission_id: The ID of the submission.
    :return: JSON object representing the combined questions, or an error message.
    '''

    # Step 1: Retrieve the submission
    submission = db.session.execute(select(Submission).filter_by(submission_id=submission_id)).scalar_one_or_none()
    
    if submission is None:
        return {"message": "Submission not found."}, 400
    
    # Step 2: Retrieve the generated question file details from the database
    question_files_generated = db.session.execute(
        select(GeneratedQnFile).filter_by(submission_id=submission_id)
    ).scalars()
    
    if not question_files_generated:
        return {"message": f"No question file found for submission ID {submission_id}."}, 404
    all_questions_files = []
    try:
        for question_file_generated in question_files_generated:
        # Get the S3 file path
            question_file_path = question_file_generated.generated_qn_file_path

            # Step 3: Use the get_file function to fetch the file from S3
            status, file = get_file(question_file_path)

            if status == FileStatus.BAD_PATH:
                return {"message": f"File {question_file_path} not found in S3."}, 404
            elif status == FileStatus.BAD_EXTENSION:
                return {"message": "File has an invalid extension."}, 400
            elif status == FileStatus.UNKNOWN_ERR:
                return {"message": "An unknown error occurred while retrieving the file from S3."}, 500

            # Step 4: Load the outer JSON from the file-like object
            combined_questions = json.load(file)

            # Step 5: Check for double-encoded fields and decode them if necessary
            if isinstance(combined_questions, list):
                combined_questions = combined_questions[0] if combined_questions else {}
            
            if isinstance(combined_questions.get('static_questions'), str):
                combined_questions['static_questions'] = json.loads(combined_questions['ai_questions'])
            
            if isinstance(combined_questions.get('random_questions'), str):
                combined_questions['random_questions'] = json.loads(combined_questions['ai_questions'])

            if isinstance(combined_questions.get('ai_questions'), str):
                combined_questions['ai_questions'] = json.loads(combined_questions['ai_questions'])
            all_questions_files.append(combined_questions)

        return all_questions_files, 200

    except Exception as e:
        traceback.print_exc()
        return {"message": f"An error occurred while retrieving questions for submission ID {submission_id}.", "error": str(e)}, 500

def get_job_status(job_id):
    try:
        # Query the job status from the JobSubsystem
        job_status = get_job_status(job_id)  

        # Check if current job status
        if job_status == SubsystemStatus.COMPLETED_JOB:
            return {
                "message": "Question generation is completed.",
                "job_id": job_id,
                "status": "COMPLETED", 
            }, 200
        elif job_status == SubsystemStatus.AWAITING_INSTANCE:
            return {
                "message": "Question generation is in progress.",
                "job_id": job_id, 
                "status": "IN_PROGRESS"
            }, 200
        else:
            return {
                "message": "Question generation failed.",
                "job_id": job_id, 
                "status": "FAILED"
            }, 200
    except Exception as e :
            return {"message": "An error occurred while getting the status.", "error": str(e)}, 500

#TODO => Check if pdf is being generated from the JSON file stored on disk
def download_questions(submission_id):
    '''
      Download the generated questions for a specific submission.

      :param submission_id: The ID of the submission
      :return generated question pdf file
    '''
    # Step 1: Retrieve the submission from the database using submission_id
    submission = db.session.execute(select(Submission).filter_by(submission_id=submission_id)).scalar_one_or_none()
    
    if submission is None:
        return {"message": "Submission not found"}, 404

    # Step 2: Retrieve the generated question file details
    question_details = db.session.execute(select(GeneratedQnFile).filter_by(submission_id=submission_id)).scalar_one_or_none()

    if question_details is None:
        return {"message": "Generated question file not found for this submission"}, 404

    # Step 3: Get the file path from the question details
    question_file_path = question_details.generated_qn_file_path

    # Step 4: Get the file from the file System
    question_file = get_file(question_file_path)

    try:
        # https://flask.palletsprojects.com/en/3.0.x/api/ 
        # Step 5: Send the file as an attachment for download
        return send_file(question_file , as_attachment=True), 200
    except Exception as e:
        return {"message": f"An error occurred while downloading the generated questions for submission ID {submission_id}", "error": str(e)}, 500


def package_all_questions(submission_id, ai_questions):
    """
    Package static questions, random questions from the question bank, and AI-generated questions 
    into a single JSON file and save it to disk or S3.
    :param submission_id: The ID of the submission
    :param unit_code: The unit code of the project
    :param project_title: The title of the project
    :param ai_questions: A list of AI-generated questions
    :return: The path to the generated JSON file
    """
    
    # Step 1: Retrieve the submission based on the submission_id
    submission = db.session.execute(select(Submission).filter_by(submission_id=submission_id)).scalar_one_or_none()
    # Step 1.1: Retrieve the project the submission is under
    project = submission.for_project
    if project is None:
        return {"message": "Project not found"}, 404
    # Step 2: Get static questions from the project model
    static_questions = project.static_questions
    if not isinstance(static_questions, list):
        return {"message": "Static questions should be a list."}, 400
    # Step 3: Get random questions from the question bank using the existing method in the Project model
    random_questions = project.get_random_questions_from_bank()
    if not isinstance(random_questions, list):
        return {"message": "Random questions should be a list."}, 400
    # Step 4: Check ai questions format
    #if isinstance(ai_questions, dict):
        # Convert dictionary to a list of category-based dictionaries
        #ai_questions = convert_ai_questions_to_list(ai_questions)
    # Step 5: Combine all questions into a single dictionary
    combined_questions = {
        "submission_id": submission_id,
        "unit_code": project.unit_code,
        "project_title": project.project_name,
        "static_questions": static_questions,
        "random_questions": random_questions,
        "ai_questions": ai_questions
    }
    return combined_questions
