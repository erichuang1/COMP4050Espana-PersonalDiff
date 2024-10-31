from src.db_instance import db
from src.main import create_app
from src.models.models_all import *

  
def insert_if_not_exists(model, **kwargs):
    """
    Inserts a new record into the database only if it doesn't already exist.
    :param model: The SQLAlchemy model to query.
    :param kwargs: The fields to check for existence.
    :return: The instance (existing or new).
    """
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        print(f"{model.__name__} already exists with {kwargs}.")
        return instance
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        print(f"Inserted new {model.__name__} with {kwargs}.")
        return instance

def insert_data():
    """
    Inserts test data into the Staff, Unit, Project, StudentCSV, Submission, and GeneratedQnFile tables.
    Inserts only if the record does not already exist in the database.
    """
    # Insert Staff (Conveners and TAs)
    convener1 = insert_if_not_exists(Staff, staff_email="convener1@example.com", staff_name="Dr. Convener 1", staff_type="Convener")
    convener2 = insert_if_not_exists(Staff, staff_email="convener2@example.com", staff_name="Dr. Convener 2", staff_type="Convener")
    convener3 = insert_if_not_exists(Staff, staff_email="convener3@example.com", staff_name="Dr. Convener 3", staff_type="Convener")
    ta1 = insert_if_not_exists(Staff, staff_email="ta1@example.com", staff_name="Teaching Assistant 1", staff_type="TA")
    ta2 = insert_if_not_exists(Staff, staff_email="ta2@example.com", staff_name="Teaching Assistant 2", staff_type="TA")
    ta3 = insert_if_not_exists(Staff, staff_email="ta3@example.com", staff_name="Teaching Assistant 3", staff_type="TA")
    ta4 = insert_if_not_exists(Staff, staff_email="ta4@example.com", staff_name="Teaching Assistant 4", staff_type="TA")
    ta5 = insert_if_not_exists(Staff, staff_email="ta5@example.com", staff_name="Teaching Assistant 5", staff_type="TA")

    # # Insert Units
    unit1 = insert_if_not_exists(Unit, unit_code="CS101", unit_name="Intro to Computer Science", unit_session="S1", unit_year=2024, convener_id=convener1.staff_id, unit_level= "First Year")
    unit2 = insert_if_not_exists(Unit, unit_code="CS102", unit_name="Data Structures", unit_session="S1", unit_year=2024, convener_id=convener2.staff_id, unit_level= "First Year")
    unit3 = insert_if_not_exists(Unit, unit_code="CS103", unit_name="Algorithms", unit_session="S1", unit_year=2024, convener_id=convener3.staff_id, unit_level= "First Year")
    unit4 = insert_if_not_exists(Unit, unit_code="CS104", unit_name="Operating Systems", unit_session="S1", unit_year=2024, convener_id=convener1.staff_id, unit_level= "First Year")
    unit5 = insert_if_not_exists(Unit, unit_code="CS105", unit_name="Database Systems", unit_session="S1", unit_year=2024, convener_id=convener2.staff_id, unit_level= "First Year")
    # Insert Projects
    #project1 =  insert_if_not_exists(Project, unit_code="CS101", project_name="Project 1", static_questions_count=5, questions_difficulty = 'Hard')
    #project2 =  insert_if_not_exists(Project, unit_code="CS102", project_name="Project 2", static_questions_count=5, questions_difficulty = 'Hard')
    #project3 =  insert_if_not_exists(Project, unit_code="CS103", project_name="Project 3", static_questions_count=5, questions_difficulty = 'Easy')
    #project4 =  insert_if_not_exists(Project, unit_code="CS104", project_name="Project 4", static_questions_count=5, questions_difficulty = 'Hard')
    #project5 =  insert_if_not_exists(Project, unit_code="CS105", project_name="Project 5", static_questions_count=5, questions_difficulty = 'Medium')
    
    #     # Insert Projects with all the required parameters
    # project1 = insert_if_not_exists(
    #     Project, 
    #      unit_code="CS101", 
    #      project_name="Project 1", 
    #      questions_difficulty='Hard',
    #      question_bank_count=10,
    #      factual_recall_count=2,
    #      conceptual_understanding_count=2,
    #      analysis_evaluation_count=1,
    #      application_problem_solving_count=1,
    #      open_ended_discussion_count=1
    #  )

    # project2 = insert_if_not_exists(
    #     Project, 
    #     unit_code="CS102", 
    #     project_name="Project 2", 
    #     questions_difficulty='Hard',
    #     question_bank_count=8,
    #     factual_recall_count=1,
    #     conceptual_understanding_count=1,
    #     analysis_evaluation_count=1,
    #     application_problem_solving_count=1,
    #     open_ended_discussion_count=1
    # )

    # project3 = insert_if_not_exists(
    #     Project, 
    #     unit_code="CS103", 
    #     project_name="Project 3", 
    #     questions_difficulty='Easy',
    #     question_bank_count=6,
    #     factual_recall_count=2,
    #     conceptual_understanding_count=1,
    #     analysis_evaluation_count=1,
    #     application_problem_solving_count=0,
    #     open_ended_discussion_count=0
    # )

    # project4 = insert_if_not_exists(
    #     Project, 
    #     unit_code="CS104", 
    #     project_name="Project 4", 
    #     questions_difficulty='Hard',
    #     question_bank_count=12,
    #     factual_recall_count=1,
    #     conceptual_understanding_count=1,
    #     analysis_evaluation_count=1,
    #     application_problem_solving_count=1,
    #     open_ended_discussion_count=2
    # )

    # project5 = insert_if_not_exists(
    #     Project, 
    #     unit_code="CS105", 
    #     project_name="Project 5", 
    #     questions_difficulty='Medium',
    #     question_bank_count=7,
    #     factual_recall_count=2,
    #     conceptual_understanding_count=2,
    #     analysis_evaluation_count=1,
    #     application_problem_solving_count=1,
    #     open_ended_discussion_count=1
    # )
    
    rubric1 = insert_if_not_exists (RubricGenerated,
        rubric_title="Rubric for Assignment 1",
        rubric_json_s3_file_name="assignment1_rubric.json",
        rubric_json_s3_file_path="s3://rubrics/assignment1_rubric.json",
        rubric_generation_status="Completed",
        created_by_learning_design_staff_id=convener1.staff_id
    )

    rubric2 = insert_if_not_exists(RubricGenerated,
        rubric_title="Rubric for Assignment 2",
        rubric_json_s3_file_name="assignment2_rubric.json",
        rubric_json_s3_file_path="s3://rubrics/assignment2_rubric.json",
        rubric_generation_status="Completed",
        created_by_learning_design_staff_id=convener1.staff_id
    )

    rubric3 = insert_if_not_exists(RubricGenerated,
        rubric_title="Rubric for Final Exam",
        rubric_json_s3_file_name="final_exam_rubric.json",
        rubric_json_s3_file_path="s3://rubrics/final_exam_rubric.json",
        rubric_generation_status="Completed",
        created_by_learning_design_staff_id=convener1.staff_id
    )


    # # Commit Projects first to avoid foreign key constraint errors in Submission
    # db.session.add_all([convener1, convener2, convener3, ta1, ta2, ta3, ta4, ta5])
    # db.session.add_all([unit1, unit2, unit3, unit4, unit5])
    # db.session.add_all([project1, project2, project3, project4, project5])
    # db.session.commit()

    # # Insert StudentCSV
    # student_csv1 = StudentCSV(studentcsv_file_name="students_cs101.csv", studentcsv_file_path="/path/students_cs101.csv", project_id=1, unit_code="CS101")
    # student_csv2 = StudentCSV(studentcsv_file_name="students_cs102.csv", studentcsv_file_path="/path/students_cs102.csv", project_id=2, unit_code="CS102")
    # student_csv3 = StudentCSV(studentcsv_file_name="students_cs103.csv", studentcsv_file_path="/path/students_cs103.csv", project_id=3, unit_code="CS103")
    # student_csv4 = StudentCSV(studentcsv_file_name="students_cs104.csv", studentcsv_file_path="/path/students_cs104.csv", project_id=4, unit_code="CS104")
    # student_csv5 = StudentCSV(studentcsv_file_name="students_cs105.csv", studentcsv_file_path="/path/students_cs105.csv", project_id=5, unit_code="CS105")

    # # Insert Submissions
    # submission1 = Submission(submission_file_name="submission1.pdf", submission_file_path="/uploads/submission1.pdf", submission_status="Submitted", uploader_id=3, project_id=1, unit_code="CS101")
    # submission2 = Submission(submission_file_name="submission2.pdf", submission_file_path="/uploads/submission2.pdf", submission_status="Graded", uploader_id=3, project_id=2, unit_code="CS102")
    # submission3 = Submission(submission_file_name="submission3.pdf", submission_file_path="/uploads/submission3.pdf", submission_status="Submitted", uploader_id=4, project_id=3, unit_code="CS103")
    # submission4 = Submission(submission_file_name="submission4.pdf", submission_file_path="/uploads/submission4.pdf", submission_status="Graded", uploader_id=5, project_id=4, unit_code="CS104")
    # submission5 = Submission(submission_file_name="submission5.pdf", submission_file_path="/uploads/submission5.pdf", submission_status="Submitted", uploader_id=2, project_id=5, unit_code="CS105")

    # # Insert Generated Question Files
    # qn_file1 = GeneratedQnFile(generated_qn_file_name="questions1.pdf", generated_qn_file_path="/uploads/questions1.pdf", submission_id=1)
    # qn_file2 = GeneratedQnFile(generated_qn_file_name="questions2.pdf", generated_qn_file_path="/uploads/questions2.pdf", submission_id=2)
    # qn_file3 = GeneratedQnFile(generated_qn_file_name="questions3.pdf", generated_qn_file_path="/uploads/questions3.pdf", submission_id=3)
    # qn_file4 = GeneratedQnFile(generated_qn_file_name="questions4.pdf", generated_qn_file_path="/uploads/questions4.pdf", submission_id=4)
    # qn_file5 = GeneratedQnFile(generated_qn_file_name="questions5.pdf", generated_qn_file_path="/uploads/questions5.pdf", submission_id=5)

    # # Add remaining data and commit
    # db.session.add_all([student_csv1, student_csv2, student_csv3, student_csv4, student_csv5])
    # db.session.add_all([submission1, submission2, submission3, submission4, submission5])
    # db.session.add_all([qn_file1, qn_file2, qn_file3, qn_file4, qn_file5])
    # db.session.commit()

    # db.session.add_all([convener1, convener2, convener3, ta1, ta2, ta3, ta4, ta5])  
    # Commit the session to persist data in the database
    # db.session.commit()

    print("Data inserted successfully!")

