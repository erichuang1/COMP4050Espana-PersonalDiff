import pytest
from src.main import create_app
from src.db_instance import db
from src.models.models_all import *
from insert_data import insert_data

import json
import src.controllers.rubric_queries as rq
import src.job_subsystem as js
import src.file_management as fm

@pytest.fixture(scope='function')
def app():
    app = create_app()
    with app.app_context():
        # Initialize the database
        db.drop_all()
        db.create_all()
        insert_data()
        yield app

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function', autouse=True)
def initialize_rubric_sample(client):
    response = client.get('/initialise_rubric_sample')
    assert response.status_code == 200

# Test Rubric Endpoints
def test_rubric_download(client):
    with client.application.app_context():
        # # @rubric.route('/initialise_rubric_sample')
        # staff_email = "convener1@example.com"
        # with open('C:\\test\\rubric.json', 'r') as file:
        #     rubric_dict = json.load(file)
        # js.test_submit_new_rubric_job(staff_email, "assessment1", None, None, json.dumps(rubric_dict))
        # status, s3_path = fm.create_json_file(rubric_dict.get("rubric_title") + ".json", rubric_dict, rename=False)
        # rq.upload_generated_rubric(staff_email, "title1", 'rubric.json', s3_path, js.SubsystemStatus.OKAY)

        # Now test the /download_rubric endpoint
        response = client.get('/download_rubric/4/pdf')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/pdf'

        # Save the file for manual inspection
        # with open('rubric.pdf', 'wb') as f:
        #     f.write(response.data)

        assert len(response.data) > 0

