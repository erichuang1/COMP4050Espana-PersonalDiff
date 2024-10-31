from flask import Blueprint

from .unit_routes import unit
from .project_routes import project
from .collaborator_routes import collaborator
from .auth_routes import auth
from .student_routes import student
from .submission_routes import submission
from .questions_routes import question
from .question_bank_routes import question_bank
from .test_routes import test
from .rubric_routes import rubric
from .marking_guide_routes import marking_guide

def register_blueprints(app):
    """
    Register all route blueprints with the Flask app.
    """
    app.register_blueprint(unit)
    app.register_blueprint(project)
    app.register_blueprint(collaborator)
    app.register_blueprint(auth)
    app.register_blueprint(test)
    app.register_blueprint(student)
    app.register_blueprint(submission)
    app.register_blueprint(question)
    app.register_blueprint(rubric)
    app.register_blueprint(question_bank)
    app.register_blueprint(marking_guide)
