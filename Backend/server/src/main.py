from flask import Flask
from flask_cors import CORS
from src.routes import register_blueprints
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from src.db_instance import db  # Import the db object from the new db.py file
from src.file_management import initialise as fileinitialise
from src.job_subsystem import initialise  as jobinitialise
import app_config
import os
from flask_migrate import Migrate
import boto3
from dotenv import load_dotenv

def create_app(test_config = None):
    print("Creating app...")
    app = Flask(__name__)
    # Load the S3 bucket name from environment variables
    s3_bucket_name = os.getenv("S3_BUCKET_NAME")
    # Initialize the S3 client using the IAM role (no credentials needed)
    s3 = boto3.client('s3')
    fileinitialise(s3, s3_bucket_name)
    jobinitialise(1, 1, False, s3, s3_bucket_name)    
    app.config.from_object(app_config)
    CORS(app)
    if test_config is not None:
        app.config.from_mapping(test_config)

    register_blueprints(app)
    db.init_app(app)
    # migrate = Migrate(app, db)
    print("App created")
    return app
