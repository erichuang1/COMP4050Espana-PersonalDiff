from sqlalchemy import select, delete

from src.db_instance import db
from src.models.models_all import *
import src.file_management as fm

def create_project(unit_code, data):
    """
    Create a new assignment (project) within a specific unit.
    :param unit_code: The code of the unit for which the assignment needs to created
    :param data: Containing assignment details (name, year, session)
    :return: JSON object with details of the created assignment or an error message

    """
    project_name = data.get("project_name")

    # Check if a project with the same name already exists within the unit
    existing_project = db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_name)).scalar_one_or_none()
    if existing_project is not None:
        return {"message": f"Project already exists within in unit {unit_code}."}, 400

    # Create a new project 
    new_project = Project(
        unit_code = unit_code,
        project_name = project_name
    )

    try:
        db.session.add(new_project)
        db.session.commit()
        return {
            "message": "Project created successfully.",
            "project": {
                "project_id": new_project.project_id,
                "unit_code": new_project.unit_code,
                "project_name": new_project.project_name
            }
        }, 201
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while creating the project.", "error": str(e)}, 500

def get_project_details(unit_code, project_title):
    """
    Retrieve details of a specific assignment (project) within a unit.

    :param unit_code: The code of the unit the assignment belongs to
    :param project_title: The title of the assignment to retrieve
    :return: JSON object with project details or an error message

    """
    try:
        # Retrieve project
        project = db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_title)).scalar_one_or_none()

        # If project does not exist, return error message
        if project is None:
            return {"message": f"Project not found in unit {unit_code}."}, 404

        # If exists, then return the project details with success message
        return {
            "project_id": project.project_id,
            "unit_code": project.unit_code,
            "project_name": project.project_name
        }, 200
    except Exception as e:
        return {"message": "An error occurred while retrieving the assignment.", "error": str(e)}, 500

def update_project_details(unit_code, project_title, data):
    """
    Update details of an existing assignment (project) within a unit.

    :param unit_code: The code of the unit the assignment belongs to
    :param project_title : The title of the assignment to update
    :param data: Contains updated project details
    :return: JSON object with updated project details or an error message
    """

    # Retrieve project
    project = db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_title)).scalar_one_or_none()

    # If project does not exist, return error message
    if project is None:
        return {f"message": "Project not found in unit {unit_code}."}, 404

    # Update project details
    if "project_name" in data:
        project.project_name = data["project_name"]

    # Return the updates project details with a success message
    try:
        db.session.commit()
        return {
            "message": "Project updated successfully.",
            "project": {
                "project_id": project.project_id,
                "unit_code": project.unit_code,
                "project_name": project.project_name
            }
        }, 200
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while updating the assignment.", "error": str(e)}, 500

def delete_project_from_db(unit_code, project_title):
    """
    Delete a specific assignment (project) by its title within a unit.

    :param unit_code: The code of the unit the assignment belongs to
    :param project_title: The title of the assignment to delete
    :return: Message indicating success or failure

    """
    try:
        # Step 1: Retrieve project
        project =  db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_title)).scalar_one_or_none()

        # Step 2: If project does not exist, return error message
        if project is None:
            return {"message": f"Project not found in unit {unit_code}."}, 404
        
        # Step 3: Retrieve all the submissions for the project
        submissions = db.session.execute(select(Submission).filter_by(project_id=project.project_id)).scalars()

        # Step 4: For each submission
        for submission in submissions:
            # Step 4a:  Retrieve all the question generated files for the submission
            generated_qn_files = db.session.execute(select(GeneratedQnFile).filter_by(submission_id=submission.submission_id)).scalars()
            # Step 4b: Delete the file, using file system management
            for generated_qn_file in generated_qn_files:
                file_status = fm.del_file(generated_qn_file.generated_qn_file_name)

                if file_status == fm.FileStatus.OKAY:
                    print("File deleted successfully.")
                else:
                    print(f"Failed to delete file. Status: {file_status.name}")

                # Step 4c: Delete the file details from the database
                db.session.delete(generated_qn_file)

            # Step 5: Delete the submission 
            db.session.delete(submission)

        # Step 6: Delete the project and commmit
        db.session.delete(project)
        db.session.commit()

        return {"message": "Project deleted successfully."}, 200
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while deleting the assignment.", "error": str(e)}, 500

def create_project_questions_template(unit_code, project_title, data):
    '''
        Create an questions template for specific project
        :param unit_code : The code of the unit for which the assignment needs to created.
        :param project_title : The title of the assignment to retrieve.
        :param data: Dictionary containing template details (static_questions, question_bank_count,...)
        :return: JSON object with project details (includes template data) or an error message
    '''
    # Retrieve project
    project = db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_title)).scalar_one_or_none()

    # If project does not exist, return error message
    if project is None:
        return {f"message": "Project not found in unit {unit_code}."}, 404
    
    # Add to Project db
    static_questions = data.get('static_questions')
    project.set_static_questions(static_questions)

 
    project.question_bank_count = data.get('question_bank_count')
    project.factual_recall_count = data.get('factual_recall_count')
    project.conceptual_understanding_count = data.get('conceptual_understanding_count')
    project.analysis_evaluation_count = data.get('analysis_evaluation_count')
    project.application_problem_solving_count = data.get('application_problem_solving_count')
    project.open_ended_discussion_count = data.get('open_ended_discussion_count')
    project.questions_difficulty = data.get('questions_difficulty')

    # Return the updates project details with a success message
    try:
        db.session.commit()
        return {
            "message": "Questions Template added successfully.",
            "project": {
                "project_id": project.project_id,
                "unit_code": project.unit_code,
                "project_name": project.project_name,
                "static_question": project.static_questions,
                "question_bank_count": project.question_bank_count,
                "factual_recall_count": project.factual_recall_count,
                "conceptual_understanding_count": project.conceptual_understanding_count,
                "analysis_evaluation_count": project.analysis_evaluation_count,
                "application_problem_solving_count": project.application_problem_solving_count,
                "open_ended_discussion_count": project.open_ended_discussion_count,
                "questions_difficulty": project.questions_difficulty
            }
        }, 200
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while adding questions template for the project.", "error": str(e)}, 500

def update_questions_template(unit_code, project_title, data):
    '''
        Update the questions template for specific project
        :param unit_code : The code of the unit for which the assignment needs to created.
        :param project_title : The title of the assignment to retrieve.
        :param data: Dictionary containing template details (static_questions, question_bank_count,...)
        :return: JSON object with project details (includes template data) or an error message
    '''
    # Retrieve project
    project = db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_title)).scalar_one_or_none()

    # If project does not exist, return error message
    if project is None:
        return {f"message": "Project not found in unit {unit_code}."}, 404
    

    if "static_questions" in data:
        project.set_static_questions(data["static_questions"]) 

    if "question_bank_count" in data:
        project.question_bank_count = data["question_bank_count"]

    if "factual_recall_count" in data:
        project.factual_recall_count = data["factual_recall_count"]
    if "conceptual_understanding_count" in data:
        project.conceptual_understanding_count = data["conceptual_understanding_count"]
    if "analysis_evaluation_count" in data:
        project.analysis_evaluation_count = data["analysis_evaluation_count"]
    if "application_problem_solving_count" in data:
        project.application_problem_solving_count = data["application_problem_solving_count"]
    if "open_ended_discussion_count" in data:
        project.open_ended_discussion_count = data["open_ended_discussion_count"]
    if "questions_difficulty" in data:
        project.questions_difficulty = data["questions_difficulty"]

    # Return the updates questions template details with a success message
    try:
        db.session.commit()
        return {
            "message": "Questions Template updated successfully.",
            "project": {
                "project_id": project.project_id,
                "unit_code": project.unit_code,
                "project_name": project.project_name,
                "static_question": project.static_questions,
                "question_bank_count": project.question_bank_count,
                "factual_recall_count": project.factual_recall_count,
                "conceptual_understanding_count": project.conceptual_understanding_count,
                "analysis_evaluation_count": project.analysis_evaluation_count,
                "application_problem_solving_count": project.application_problem_solving_count,
                "open_ended_discussion_count": project.open_ended_discussion_count,
                "questions_difficulty": project.questions_difficulty
            }
        }, 200
    except Exception as e:
        db.session.rollback()
        return {"message": "An error occurred while updating the questions template for the project.", "error": str(e)}, 500

def retrieve_questions_template(unit_code, project_title):
    try:
        # Retrieve project
        project = db.session.execute(select(Project).filter_by(unit_code=unit_code, project_name=project_title)).scalar_one_or_none()

        # If project does not exist, return error message
        if project is None:
            return {f"message": "Project not found in unit {unit_code}."}, 404
        
        # Check if the project template is uninitialised or empty
        if (project.static_questions is None or project.static_questions == []) and \
           project.question_bank_count == 0 and \
           project.factual_recall_count == 0 and \
           project.conceptual_understanding_count == 0 and \
           project.analysis_evaluation_count == 0 and \
           project.application_problem_solving_count == 0 and \
           project.open_ended_discussion_count == 0:

            # Return message that the template is not added
            return {
                "message": "Project template not added.",
                "project": {
                    "project_id": project.project_id,
                    "unit_code": project.unit_code,
                    "project_name": project.project_name,
                    "static_question": project.static_questions if project.static_questions else "",
                    "question_bank_count": "",
                    "factual_recall_count": "",
                    "conceptual_understanding_count": "",
                    "analysis_evaluation_count": "",
                    "application_problem_solving_count": "",
                    "open_ended_discussion_count": "",
                    "questions_difficulty": project.questions_difficulty
                }
            }, 200

        # If exists, then return the project template details with success message
        return {
            "project": {
                "project_id": project.project_id,
                "unit_code": project.unit_code,
                "project_name": project.project_name,
                "static_question": project.static_questions,
                "question_bank_count": project.question_bank_count,
                "factual_recall_count": project.factual_recall_count,
                "conceptual_understanding_count": project.conceptual_understanding_count,
                "analysis_evaluation_count": project.analysis_evaluation_count,
                "application_problem_solving_count": project.application_problem_solving_count,
                "open_ended_discussion_count": project.open_ended_discussion_count,
                "questions_difficulty": project.questions_difficulty
            }
        }, 200
    except Exception as e:
        return {"message": "An error occurred while retrieving the questions template for the project.", "error": str(e)}, 500

def fetch_all_projects_from_unit(unit_code):
    """
    Retrieve details of a all projects within a unit.

    :param unit_code: The code of the unit the assignment belongs to
    :return: JSON object with project details of all the projects or an error message

    """
    # Retrieve project
    projects = db.session.execute(select(Project).filter_by(unit_code=unit_code)).scalars()
    all_projects_for_unit = []
    for project in projects:
    # If project does not exist, return error message
        if project is None:
            return {f"message": "Project not found in unit {unit_code}."}, 404
        all_projects_for_unit.append({
            "project_id": project.project_id,
            "unit_code": project.unit_code,
            "project_name": project.project_name
        })
    try:
        return all_projects_for_unit, 200
    except Exception as e:
        return {"message": "An error occurred while retrieving all the projects for this unit.", "error": str(e)}, 500