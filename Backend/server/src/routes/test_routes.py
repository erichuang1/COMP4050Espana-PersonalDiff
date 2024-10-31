import json
import os
from flask import Blueprint, jsonify

test = Blueprint('test', __name__)

import src.controllers.rubric_queries as rq
import src.job_subsystem as js
import src.file_management as fm

@test.route('/')
def home():
    return "Hello Mif this works"

@test.route('/initialise_rubric_sample')
def initialise_rubric_sample():
    try:
        staff_email = "convener1@example.com"
        file_path = 'C:\\test\\rubric.json'
        if not os.path.exists(file_path):
            file_path = '/app/files/rubric.json'
        with open(file_path, 'r') as file:
            rubric_dict = json.load(file)
        # js.test_submit_new_rubric_job(staff_email, "assessment1", None, None, json.dumps(rubric_dict))
        status, s3_path = fm.create_json_file(rubric_dict.get("rubric_title") + ".json", rubric_dict, rename=False)
        rq.upload_generated_rubric(staff_email, "title1", 'rubric.json', s3_path, js.SubsystemStatus.OKAY)
        return "Completed.", 200
    except Exception as e:
        return jsonify({"message: An error occured while initialising sample rubric." "error": str(e)}), 500