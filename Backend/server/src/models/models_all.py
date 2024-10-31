import csv
import io
import random
from ..db_instance import db
from typing import List, Optional
from sqlalchemy import JSON, BigInteger, Column, Table, ForeignKey, String, ForeignKeyConstraint, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from sqlalchemy.ext.mutable import MutableList
from src.file_management import get_file, FileStatus
# https://flask.palletsprojects.com/en/3.0.x/patterns/sqlalchemy/#flask-sqlalchemy-extension
# https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers/
# https://flask-sqlalchemy.palletsprojects.com/en/2.x/models/
# https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#one-to-one
# https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#many-to-many
# https://docs.sqlalchemy.org/en/20/orm/inheritance.html
# https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html#declarative-table-with-mapped-column
    

# A SQLAlchemy model to store the session data
class Session(db.Model):
    __tablename__ = 'session'

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # Session ID
    session_data: Mapped[str] = mapped_column(String(255))  # Store session data as a string
    expiry: Mapped[Optional[datetime]] = mapped_column()  # Expiry time for the session

    def __repr__(self):
        return f"<Session id={self.id} expires={self.expiry}>"

    
# Table that was created due to the M:N rs between TeachingAssistant & Unit d
ta_added_to_unit = Table(
    "ta_added_to_unit",
    db.Model.metadata,
    Column("unit_code", ForeignKey("unit.unit_code"), primary_key = True),
    Column("staff_id", ForeignKey("staff.staff_id"), primary_key = True),
    Column("ta_role_in_unit", String(50))
    # extend_existing=True # Allow redefinition of the table  
     
)

class Staff(db.Model):
    __tablename__ = 'staff'

    staff_id: Mapped[int] = mapped_column(primary_key=True) # Auto Incremented (Surrogate key)
    staff_email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  
    staff_name: Mapped[str] = mapped_column(String(50))
    # To get this, frontend people need to have a form that asks them if they are a TA or a Convener
    staff_type: Mapped[str] = mapped_column(String(50)) 
    
    # Relationships:
    # This list can be empty (NOT NULL), as there are staff members that do not upload any student submissions
        # So, no need to use optional
    submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates="uploaded_by")
    units_ta: Mapped[List["Unit"]] = relationship("Unit", 
        secondary= ta_added_to_unit, back_populates="teachingassistants") # M:N rs between TA and Unit 
    units_convener: Mapped[List["Unit"]] = relationship("Unit", back_populates="unit_convener") # one to many rs between Convener & Unit
      # One-to-many relationship: A staff member can create multiple rubrics
    generated_rubrics: Mapped[List["RubricGenerated"]] = relationship("RubricGenerated", back_populates="created_by")
    # __table_args__ = {'extend_existing': True}  # Allow redefinition of the table
    def __repr__(self):
        return f'<Staff {self.staff_name!r}>'


class Unit(db.Model):
    __tablename__= 'unit'
    unit_code: Mapped[str] = mapped_column(String(10),primary_key=True)
    unit_name: Mapped[str]= mapped_column(String(50))
    unit_session: Mapped[str] = mapped_column(String(50))
    unit_year: Mapped[int]
    unit_level: Mapped[str] = mapped_column(String(50))
    convener_id: Mapped[int] = mapped_column(ForeignKey("staff.staff_id"))
    # Relationships
    unit_convener: Mapped["Staff"] = relationship("Staff",back_populates="units_convener") # one to many rs between Convener & Unit
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="unit_under") # one to many rs between Unit & Project
    studentcsvs: Mapped[List["StudentCSV"]] = relationship("StudentCSV", back_populates="unit_under") # 1-M rs between Unit & StudentCSV
    teachingassistants: Mapped[List["Staff"]] = relationship("Staff", 
        secondary=ta_added_to_unit, back_populates="units_ta") # M:N rs between TeachingAssistant & Unit
    # __table_args__ = {'extend_existing': True}  # Allow redefinition of the table
    def __repr__(self):
        return f'<Unit {self.unit_code!r}'

class Project(db.Model):
    __tablename__ ='project'
    # Composite primary key (CPK)
    # Adding autoincrement as SQLAlchemy does not implicitly do it for CPK
    project_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    unit_code: Mapped[str] = mapped_column(String(10), ForeignKey("unit.unit_code"), primary_key=True)
    project_name: Mapped[str] = mapped_column(String(50))
    # # Stores the number of static questions specified by the user
    # static_questions_count: Mapped[int] = mapped_column(default=0)
    # Stores the list of static questions as JSON
    static_questions: Mapped[List] = mapped_column(MutableList.as_mutable(JSON), default=list)
    # Stores the number of QnBank questions specified by the user
    question_bank_count: Mapped[int] = mapped_column(default=0) 
    # Stores the number of AI generated questions specified by the user
    # ai_questions_count: Mapped[int] = mapped_column( default=0)
    # Fields for different types of AI questions
    factual_recall_count: Mapped[int] = mapped_column(default=0)
    conceptual_understanding_count: Mapped[int] = mapped_column(default=0)
    analysis_evaluation_count: Mapped[int] = mapped_column(default=0)
    application_problem_solving_count: Mapped[int] = mapped_column(default=0)
    open_ended_discussion_count: Mapped[int] = mapped_column(default=0)
    # Difficulty Level for the AI questions
    questions_difficulty: Mapped[str] = mapped_column(String(50), default='Easy')
    
    # Relationships
    unit_under: Mapped["Unit"] = relationship("Unit", back_populates="projects") # one to many rs between Unit & Project
    all_submissions: Mapped[List["Submission"]] = relationship("Submission", back_populates = "for_project") # 1-M rs between Project & Submission
    qn_banks: Mapped[List["QnBank"]] = relationship("QnBank", back_populates="project", cascade="all, delete-orphan") # One-to-many rs between Project & QnBank  

    __table_args__ = (
        UniqueConstraint('project_name', 'unit_code', name='uq_project_name_per_unit'),
    )
    def __repr__(self):
        return f"<Project: unit_code='{self.unit_code}', project_name='{self.project_name}'>"

    def set_static_questions(self, questions: list):
        """Set static questions based on user input and update the count."""
        self.static_questions = questions
        # self.static_questions_count = len(questions)

    # def validate_questions_count(self) -> bool:
    #     """Validate if the number of provided questions matches the expected count."""
    #     return self.static_questions_count == len(self.static_questions)
    
    def get_random_questions_from_bank(self) -> list:
        """Randomly pick a specified number of questions from the CSV question bank file."""
        if not self.qn_banks or self.question_bank_count <= 0:
            return []
        all_questions = []
        for qn_bank in self.qn_banks:
            try: 
                # Use the get_file method to retrieve file from s3
                status, file_object = get_file(qn_bank.qnbank_file_path)
                # Check if file retrieval was successful 
                if status!= FileStatus.OKAY or file_object is None:
                    print(f"Failed to retrieve file: {qn_bank.qnbank_file_path}")
                    continue
                # If the file was retrieved successfully, read it as csv
                if isinstance(file_object, io.StringIO):
                    # reader = csv.reader(file_object)
                    # questions = [row for row in reader]
                    # all_questions.extends(questions) # Add questions to the combined questions list
                    with file_object:
                        csv_reader = csv.DictReader(file_object)
                        for row in csv_reader:
                            all_questions.append(row)
            except Exception as e:
                print(f"Error processing question bank file from s3: {e}")
                    
        if not all_questions:
            return []
        # Randomly sample the required number of questions
        return random.sample(all_questions, min(len(all_questions), self.question_bank_count))
    
class StudentCSV(db.Model):
    __tablename__ = 'studentcsv'
    studentcsv_id: Mapped[int] = mapped_column(primary_key=True)
    studentcsv_file_name: Mapped[str] = mapped_column(String(400))
    studentcsv_file_path: Mapped[str] = mapped_column(String(400))
    unit_code: Mapped[str] = mapped_column(String(10), ForeignKey("unit.unit_code"))
    # Relationships
    unit_under: Mapped["Unit"] = relationship("Unit", back_populates="studentcsvs") # 1-M rs between Unit & StudentCSV
    def __repr__(self):
        return (f"<StudentCSV(id='{self.studentcsv_id}', "
                f"file_name='{self.studentcsv_file_name}', "
                f"file_path='{self.studentcsv_file_path}', "
                f"unit_code='{self.unit_code}')>")


class Submission(db.Model):
    __tablename__= 'submission'
    submission_id : Mapped[int] = mapped_column(primary_key=True)
    submission_file_name: Mapped[str] = mapped_column(String(400))
    submission_file_path: Mapped[str] = mapped_column(String(400))
    submission_status: Mapped[str] = mapped_column(String(50))
    # Reference to the staff who uploaded the submission
    uploader_id: Mapped[int] = mapped_column(ForeignKey("staff.staff_id"))
    # Foreign keys referencing the composite primary key in the Project table
    project_id : Mapped[int] = mapped_column()
    unit_code: Mapped[str] = mapped_column(String(10))
    # Relationships
    uploaded_by: Mapped["Staff"] = relationship("Staff", back_populates="submissions") 
    generated_qn_files: Mapped[List["GeneratedQnFile"]] = relationship("GeneratedQnFile", back_populates="submission_used") # 1-M rs between Submission & GeneratedQnFile
    for_project : Mapped["Project"] = relationship("Project", back_populates="all_submissions") # 1-M rs between Project & Submission
    # As we are referring to a CPK as a foreign key. If not will expect unique items for each, rather than a combination
    __table_args__ = (
        ForeignKeyConstraint(
            [project_id, unit_code],
            ["project.project_id", "project.unit_code"]
        ),
        # {'extend_existing': True}  # Allow redefinition of the table
    )
    def __repr__(self):
        return (f"<Submission(submission_id={self.submission_id}, "
                f"file_name='{self.submission_file_name}', "
                f"uploader_id={self.uploader_id}, "
                f"project_id={self.project_id})>")

class GeneratedQnFile(db.Model):
    __tablename__= 'generatedqnfile'
    generated_qn_file_id : Mapped[int] = mapped_column(primary_key=True)
    generated_qn_file_name: Mapped[str] = mapped_column(String(400))
    generated_qn_file_path: Mapped[str] = mapped_column(String(400))
    submission_id: Mapped[int] = mapped_column(ForeignKey("submission.submission_id"))
    # Relationships:
    submission_used: Mapped["Submission"] = relationship("Submission", back_populates="generated_qn_files") # 1-M rs between Submission & GeneratedQnFile
    # _table_args__ = {'extend_existing': True}  # Allow redefinition of the table
    def __repr__(self):
        return (f"<GeneratedQnFile(generated_qn_file_id={self.generated_qn_file_id}, "
                f"file_name='{self.generated_qn_file_name}', "
                f"submission_id={self.submission_id})>")

class QnBank(db.Model):
    __tablename__ = 'qn_bank'
    # Primary key for the question bank
    qnbank_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    qnbank_file_name: Mapped[str] = mapped_column(String(400))  
    qnbank_file_path: Mapped[str] = mapped_column(String(400))
    # Foreign keys referencing the composite primary key in the Project table
    project_id : Mapped[int] = mapped_column()
    unit_code: Mapped[str] = mapped_column(String(10))

    # Relationship
    project: Mapped["Project"] = relationship("Project", back_populates="qn_banks") # 1-M rs between Project & QnBank
    
    __table_args__ = (
        ForeignKeyConstraint(
            [project_id, unit_code],
            ["project.project_id", "project.unit_code"]
        ),
    )
    def __repr__(self):
        return f"<QnBank: project_id='{self.project_id}', unit_code='{self.unit_code}', qnbank_file='{self.qnbank_file_name}'>"

class MarkingGuide(db.Model):
    __tablename__ = 'marking_guide'
    marking_guide_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    marking_guide_file_name: Mapped[str] = mapped_column(String(400))
    marking_guide_s3_file_path: Mapped[str] = mapped_column(String(400))
    marking_guide_conversion_status: Mapped[str] = mapped_column(String(50)) # Uploaded / Generated
    # When the Marking Guide is initially uploaded, this FK is allowed to be null
    # As the rubric for this Marking Guide will be generated later
    rubric_generated_from_mg: Mapped[str] = mapped_column(ForeignKey("rubric_generated.rubric_id"), nullable=True) # 1-1 rs between RubricGen and MarkingGuide
    uploaded_by_learning_design_staff_id: Mapped[int] = mapped_column(ForeignKey("staff.staff_id")) # 1-Many rs between Staff and MarkingGuide
    def __repr__(self):
        return f"<MarkingGuide: marking_guide_id: '{self.marking_guide_id}', marking_guide_file_name: '{self.marking_guide_file_name}'>"
    
    
    
        
class RubricGenerated(db.Model):
    # Technically we do not need to store the xlsx and pdf format
    # We just need to save the json we get from AI as a json file
    # And if there is a request to generate pdf or xlsx, we generate on the spot and send it
    # Rather that storing pdf/xlsx in our s3 storage
    # That way if any changes is made to the rubric, we can just change the json file content
    # Instead of having to change the pdf and xlsx as well
    # When a request comes in for a PDF or XLSX, we generate them dynamically based on the updated json file content, ensuring the latest version is always used.
    __tablename__ = 'rubric_generated'
    rubric_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rubric_title: Mapped[str] = mapped_column(String(200))
    # rubric_json: Mapped[str] = mapped_column(JSON)
    rubric_json_s3_file_name: Mapped[str] = mapped_column(String(400))
    rubric_json_s3_file_path: Mapped[str] = mapped_column(String(400))
    rubric_generation_status: Mapped[str] = mapped_column(String(50))
    # Foreign key linking to Staff (creator of the rubric)
    created_by_learning_design_staff_id: Mapped[int] = mapped_column(ForeignKey("staff.staff_id"))
    # Relationship back to Staff
    created_by: Mapped["Staff"] = relationship("Staff", back_populates="generated_rubrics")
    def __repr__(self):
        # Generate a hash value for the instance
        instance_hash = hash(self)
        
        # Create a preview of each field
        preview = (
            f"Rubric ID: {self.rubric_id} "
            f"Rubric Title: {self.rubric_title} "
            f"Rubric JSON S3 File Name: {self.rubric_json_s3_file_name} "
            f"Rubric JSON S3 File Path Path: {self.rubric_json_s3_file_path} "
        )

        return f'<RubricGenerated hash={instance_hash} preview="{preview}">'
