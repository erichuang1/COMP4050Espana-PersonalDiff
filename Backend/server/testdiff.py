# diff --git a/Backend/server/manual_tests.py b/Backend/server/manual_tests.py
# index 815c59b..772eb27 100644
# --- a/Backend/server/manual_tests.py
# +++ b/Backend/server/manual_tests.py
# @@ -23,8 +23,9 @@ testJsonFilePath = '_TESTFILES/test.json'
#  testPdfFilePath_A = '_TESTDOCUMENTS/comp3010.pdf'
#  testPdfFilePath_B = '_TESTDOCUMENTS/DUMMY_FILE.pdf'
#  testTxtFilePath = '_TESTDOCUMENTS/TEST.txt'
# -testRemoteFilePath = 's3://4050backendfilestorage/comp3010_5.pdf'
# -                       
# +
# +sampleParams = params = [ 0, 0, testPdfFilePath_A, 'ENGG3000', 'I HATE THIS UNIT', 'Hard', 'First Year', 3, 3, 3, 3, 3, 3, False, None ]
# +
#  s3 = boto3.client('s3')
#  print("Test driver running! Getting inputs:")
 
# @@ -42,37 +43,3 @@ js.initialise(1,1,False,s3,s3_bucket_name, keys)
#  js._debugUseLocalAddr = True
#  js._doSingleThread = True
#  print ("Test driver online!")
# -
# -sampleRubricCriteria = [
# -    {
# -      "criterion": "Process Management",
# -      "keywords": ["processes", "scheduling", "multithreading"],
# -      "competencies": ["understanding of process lifecycle"],
# -      "skills": ["solve synchronization issues"],
# -      "knowledge": ["scheduling algorithms", "process synchronization"]
# -    },
# -    {
# -      "criterion": "Memory Management",
# -      "keywords": ["virtual memory", "paging", "segmentation"],
# -      "competencies": ["memory allocation strategies"],
# -      "skills": ["apply virtual memory concepts"],
# -      "knowledge": ["paging", "memory allocation"]
# -    },
# -    {
# -      "criterion": "File Systems",
# -      "keywords": ["file system architecture", "file allocation"],
# -      "competencies": ["file system design"],
# -      "skills": ["optimize file systems"],
# -      "knowledge": ["file allocation methods", "disk scheduling"]
# -    }
# -  ]
# -
# -sampleUlos = [
# -    "ULO1: Understand core OS concepts like process, memory, and file systems.",
# -    "ULO2: Apply OS algorithms to solve problems.",
# -    "ULO3: Critically evaluate OS architectures.",
# -    "ULO4: Solve OS concurrency and synchronization problems."
# -  ]
# -
# -sampleParamsViva = [ 0, 0, testPdfFilePath_A, 'ENGG3000', 'I HATE THIS UNIT', 'Hard', 'First Year', 3, 3, 3, 3, 3, 3, False, None ]
# -sampleParamsRubric = [ 0, 'A complete and utter horseshit assignment. Fuck this thing.', 'hcough.mcrae@gmail.com', sampleRubricCriteria, sampleUlos ]
# diff --git a/Backend/server/src/ai/rubric_gen.py b/Backend/server/src/ai/rubric_gen.py
# index 1f4c926..9a07d3b 100644
# --- a/Backend/server/src/ai/rubric_gen.py
# +++ b/Backend/server/src/ai/rubric_gen.py
# @@ -1,31 +1,8 @@
#  from openai import OpenAI
# -from pydantic import BaseModel
 
#  # Initialise OpenAI client
#  client = None
 
# -#For Structured outputs:
# -
# -class Criteria(BaseModel):
# -   criteria_name:str
# -   criteria_description: str
# -
# -class GradeDescriptor(BaseModel):
# -    mark_min: int
# -    mark_max: int
# -    criterion: list[Criteria]
# -
# -class GradeDescriptors(BaseModel):
# -    fail: GradeDescriptor
# -    pass_: GradeDescriptor
# -    credit: GradeDescriptor
# -    distinction: GradeDescriptor
# -    high_distinction: GradeDescriptor
# -
# -class AssignmentFeedback(BaseModel):
# -    rubric_title: str
# -    grade_descriptors: GradeDescriptors
# -
#  # Method for initialising openAI client
#  def init_openai(openai_api_key, openai_org_key, openai_proj_key):
#      global client
# @@ -34,73 +11,79 @@ def init_openai(openai_api_key, openai_org_key, openai_proj_key):
#          organization=openai_org_key,
#          project=openai_proj_key
#      )
# -
# -#Helper method to get list of criterion:
# -def get_criterion(input_dict):
# -    
# -    criterion = [] #Empty list initiated to store each criteria
# -    
# -    for criteria in input_dict['criteria']:
# -        criterion.append(criteria['criterion'])
# -        
# -    return criterion
     
#  def generate_rubric(input_dict):
#      grade_descriptors = "Fail (0-49), Pass(50-64), Credit (65-74), Distinction (75-84), High Distinction (85-100)"
 
# -    assessment_criterion = get_criterion(input_dict)
# -    sys_prompt = f'''
# -    You are a highly skilled university professor responsible for creating marking rubrics for assessment tasks. You need to create a marking rubric for an assessment based on the information provided below. The grade descriptors are: {grade_descriptors}.
# -'''
# -    
# -    user_prompt = f"""
# -Assessment task overview: {input_dict['assessment_description']}
# +    prompt = f"""
# +    You are a university professor for the unit: {input_dict['unit_name']} which is a {input_dict['unit_level']} level unit. You need to create a marking rubric for an assessment based on the information provided below. The grade descriptors are: {grade_descriptors}.
# +
# +Assessment task: {input_dict['assessment_name']}
# +Assessment task overview: {input_dict['assessment_overview']}
 
# -Criterion to be assessed: {', '.join(assessment_criterion)}
# +Criterion to be assessed: {', '.join(input_dict['criteria'])}
 
# -Keywords/Competencies/Skills per Criterion which need to be taken into account:
# +Keywords/Competencies/Skills per Criterion:
#  """
 
# -    for criterion in input_dict['criteria']:
# -        user_prompt += f"{criterion['criterion']}:\n"
# -        user_prompt += "Keywords: " + ', '.join(criterion['keywords']) + "\n"
# -        user_prompt += "Competencies: " + ', '.join(criterion['competencies']) + "\n"
# -        user_prompt += "Skills: " + ', '.join(criterion['skills']) + "\n"
# -        user_prompt += "Knowledge: " + ', '.join(criterion['knowledge']) + "\n\n"
# +    for criterion, skills in input_dict['skills_per_criterion'].items():
# +        prompt += f"{criterion}:\n"
# +        for skill in skills:
# +            prompt += f"- {skill}\n"
# +        prompt += "\n"
 
# -    user_prompt += "Unit Learning Objectives (ULOs) that the assessment is mapped to:\n"
# +    prompt += "Unit Learning Objectives (ULOs) that the assessment is mapped to:\n"
#      for i, ulo in enumerate(input_dict['ulos'], 1):
# -        user_prompt += f"* {ulo}\n"
# -
# -    user_prompt += """
# -Please return the feedback in the required format.
# +        prompt += f"* ULO{i}: {ulo}\n"
# +
# +    prompt += """
# +Please return the output in the following JSON format based on the number of criterion:
# +{
# +  "assessment": "ASSESSMENT_NAME",
# +  "grade_descriptors": {
# +    "Fail (0-49)": {
# +      "CRITERION_1": "DESCRIPTION",
# +      "CRITERION_2": "DESCRIPTION",
# +      ...
# +    },
# +    "Pass (50-64)": {
# +      "CRITERION_1": "DESCRIPTION",
# +      "CRITERION_2": "DESCRIPTION",
# +      ...
# +    },
# +    "Credit (65-74)": {
# +      "CRITERION_1": "DESCRIPTION",
# +      "CRITERION_2": "DESCRIPTION",
# +      ...
# +    },
# +    "Distinction (75-84)": {
# +      "CRITERION_1": "DESCRIPTION",
# +      "CRITERION_2": "DESCRIPTION",
# +      ...
# +    },
# +    "High Distinction (85-100)": {
# +      "CRITERION_1": "DESCRIPTION",
# +      "CRITERION_2": "DESCRIPTION",
# +      ...
# +    }
# +  }
# +}
# +
# +    IMPORTANT:
# +    - Avoid the use of adjectives that are too descriptive
#      """
 
# -    completion = client.beta.chat.completions.parse(
# +    completion = client.chat.completions.create(
#          model="gpt-4o-mini",
#          messages=[
# -            {"role": "system", "content": sys_prompt},
# -            {"role": "user", "content": user_prompt}
# +            {"role": "user", "content": prompt}
#          ],
#          max_tokens=800,
# -        # response_format={"type": "json_object"}
# -        response_format=AssignmentFeedback
# +        response_format={"type": "json_object"}
#      )
 
# -    # # Parse response into dictionary:
# -    # # response = completion.choices[0].message.content
# -
# -    # # return response
# -    
# -    feedback_response = completion.choices[0].message
# -
# -    # # If the model refuses to respond, you will get a refusal message
# -    if (feedback_response.refusal):
# -        print(feedback_response.refusal)
# -        return None
# -    else:
# -        parsed= feedback_response.parsed
# -        feedback_response_json = parsed.model_dump_json()
# -        return feedback_response_json
# -
# +    # Parse response into dictionary:
# +    response = completion.choices[0].message.content
 
# +    return response
# +    
# \ No newline at end of file
# diff --git a/Backend/server/src/controllers/question_generation_queries.py b/Backend/server/src/controllers/question_generation_queries.py
# index 40877c9..771d457 100644
# --- a/Backend/server/src/controllers/question_generation_queries.py
# +++ b/Backend/server/src/controllers/question_generation_queries.py
# @@ -1,15 +1,12 @@
# -import json
#  from flask import jsonify, send_file
#  from src.db_instance import db
#  from src.models.models_all import *
#  from sqlalchemy import select, text
# -
# -# from src.file_management import *
# -import src.file_management as fm
# -# from src.job_subsystem import *
# -import src.job_subsystem as js
# +from src.file_management import *
# +from src.job_subsystem import submit_new_job, SubsystemStatus
#  import traceback
 
# +# TODO: Send the job system more information (like )
#  def generate_for_all(unit_code, project_title):
#      '''
#       Generate questions for all submission file for a specific project within a unit.
# @@ -54,11 +51,11 @@ def generate_for_all(unit_code, project_title):
 
#          #Step 4 : Send Each submission to _submit_new_job( sub_id, qns_count, unit code, level )
#          for submission in submissions:
# -            job_status, message, job_id = js.submit_new_job(submission.submission_id, submission.submission_file_path, 
# +            job_status, message, job_id = submit_new_job(submission.submission_id, submission.submission_file_path, 
#                                                  unit.unit_name,project.project_name, challengeLevel, unit.unit_level, 
#                                                  ai_questions_count, factual_recall_count, conceptual_understanding_count, analysis_evaluation_count,
#                                                  application_problem_solving_count,open_ended_discussion_count)
# -            if job_status != js.SubsystemStatus.OKAY:            
# +            if job_status != SubsystemStatus.OKAY:            
#                  return {"error": f"Failed to submit job for question generation checking status {job_status}, JobID: {job_id}, message :{str(message)}"}, 500
 
#              jobs.append({
# @@ -100,17 +97,16 @@ def generate_for_submission(unit_code, project_title, submission_id):
#      submission = db.session.execute(select(Submission).filter_by(submission_id = submission_id)).scalar_one_or_none()
     
#      # Step 4 : Send the submission to _submit_new_job( sub_id, qns_count, unit code, level )
# -    job_status, message, job_id = js.submit_new_job(submission.submission_id, submission.submission_file_path, 
# +    job_status, message, job_id = submit_new_job(submission.submission_id, submission.submission_file_path, 
#                                              unit.unit_name,project.project_name, challengeLevel, unit.unit_level, 
#                                              ai_questions_count, factual_recall_count, conceptual_understanding_count, analysis_evaluation_count,
#                                              application_problem_solving_count,open_ended_discussion_count)
#      # Step 5 : Check the job status
# -    if job_status != js.SubsystemStatus.OKAY:            
# +    if job_status != SubsystemStatus.OKAY:            
#          return {"error": f"Failed to submit job for question generation checking status {job_status}, JobID: {job_id}, message :{str(message)}"}, 500
 
#      try:
#          return{
# -            "submission_id": submission_id,
#              "message": "Submission file has been sent for Question Generation",
#              "job_status": str(job_status),
#              "job_id": job_id}, 200
# @@ -154,6 +150,8 @@ def upload_generated_files(submission_id, generated_file_name, generated_file_pa
#              db.session.rollback()
#              return {"message": "An error occurred while saving generated data to DB", "error": str(e)}, 500
     
# +#TODO: Regenerate particular questions from a submission: To be fixed using input from AI
# +#TODO: Regenerate particular questions from a submission: To be fixed using input from AI
#  def regenerate_questions(unit_code, project_title, submission_id, data):
#       '''
#        Re-Generate questions for a specific submission
# @@ -186,24 +184,24 @@ def regenerate_questions(unit_code, project_title, submission_id, data):
 
#       question_reason_list = data.get("question_reason")
 
# +     
#      # Step 4 : Send the submission to _submit_new_job( sub_id, qns_count, unit code, level ) 
# -     job_status, message, job_id = js.submit_new_job(submission.submission_id, submission.submission_file_path, 
# +     job_status, job_id = submit_new_job(submission.submission_id, submission.submission_file_path, 
#                                              unit.unit_name,project.project_name, challengeLevel, unit.unit_level, 
#                                              ai_questions_count, factual_recall_count, conceptual_understanding_count, 
#                                              analysis_evaluation_count, application_problem_solving_count, open_ended_discussion_count, 
#                                              question_reason_list)
#      # Step 5 : Check the job status
# -     if job_status != js.SubsystemStatus.OKAY:            
# -        return {"error": f"Failed to submit job for question generation checking status {job_status}, JobID: {job_id}, message :{str(message)}"}, 500
# +     if job_status != SubsystemStatus.OKAY:            
# +        return {"error": "Failed to submit job for question regeneration"}, 500
 
#       try:
#           return{
# -            "submission_id": submission_id,
#              "message": "Submission file has been sent for Question Re-Generation",
#              "job_status": str(job_status),
#              "job_id": job_id}, 200
#       except Exception as e:
# -            return {"message":f"An error occurred while regenerating questions for submission {submission_id}.", "error": str(e)}, 500
# +            return {f"message": "An error occurred while regenerating questions for submission ID submission ID {submission_id}.", "error": str(e)}, 500
 
#  def get_questions_for_submission(submission_id):
#      '''
# @@ -272,13 +270,13 @@ def get_job_status(job_id):
#          job_status = get_job_status(job_id)  
 
#          # Check if current job status
# -        if job_status == js.SubsystemStatus.COMPLETED_JOB:
# +        if job_status == SubsystemStatus.COMPLETED_JOB:
#              return {
#                  "message": "Question generation is completed.",
#                  "job_id": job_id,
#                  "status": "COMPLETED", 
#              }, 200
# -        elif job_status == js.SubsystemStatus.AWAITING_INSTANCE:
# +        elif job_status == SubsystemStatus.AWAITING_INSTANCE:
#              return {
#                  "message": "Question generation is in progress.",
#                  "job_id": job_id, 
# @@ -373,6 +371,7 @@ def package_all_questions(submission_id, ai_questions):
 
#      return combined_questions
 
# +
#  def convert_ai_questions_to_list(ai_questions):
#      """
#      Convert nested dictionary of AI questions into a list of dictionaries.
# diff --git a/Backend/server/src/controllers/rubric_queries.py b/Backend/server/src/controllers/rubric_queries.py
# index 1948df2..2566f4b 100644
# --- a/Backend/server/src/controllers/rubric_queries.py
# +++ b/Backend/server/src/controllers/rubric_queries.py
# @@ -1,15 +1,10 @@
#  import time
#  from flask import json, send_file
# -# from src.file_management import *
# +from src.file_management import *
#  from src.models.models_all import *
#  from src.db_instance import db
#  from sqlalchemy import select
 
# -# from src.file_management import *
# -import src.file_management as fm
# -# from src.job_subsystem import SubsystemStatus
# -import src.job_subsystem as js
# -
#  # Note: Performance optimisation needed for high-concurrency environment (nano-seconds). 
#  def create_rubric(data):
#      '''
# @@ -23,16 +18,19 @@ def create_rubric(data):
#                  and save it as a json file in s3 (same as what is done for question generation)
#          2. Receive 
#      '''
# -    try: 
# +
# +    '''
# +    #TODO
# +        try: 
#          # Extract the required details the AI module needs to receive for rubric generation 
#          staff_email = data.get('staff_email')
#          assessment_description = data.get('assessment_description')
#          criteria = data.get('criteria')
#          ulos = data.get('ulos')
#          # Send the `data` to the function in the job subsystem responsible for sending a rubric generation request to the AI module
# -        job_status, job_id  = js.submit_new_rubric_job(staff_email, assessment_description, criteria, ulos)
# +        job_status, job_id  = submit_new_rubric_job(staff_email, assessment_description, criteria, ulos)
 
# -        if job_status != js.SubsystemStatus.OKAY:
# +        if job_status != SubsystemStatus.OKAY:
#              return {"error": f"Failed to submit job for question generation checking status {job_status}"}, 500
         
#          response_body = {
# @@ -45,6 +43,8 @@ def create_rubric(data):
#      except Exception as e:
#          return {"message": "An error occurred while generating this rubric.", "error": str(e)}, 500
 
# +    '''
# +    pass
 
#  def upload_generated_rubric(staff_email, rubric_title, generated_rubric_file_name, generated_rubric_file_path, status):
#      '''
# @@ -94,24 +94,24 @@ def get_rubric(rubric_id):
#      try: 
#          rubric_file_path = rubric.rubric_json_s3_file_path
#          # Use the get_file function to retrieve the file from s3
# -        status, file = fm.get_file(rubric_file_path)
# -        if status == fm.FileStatus.BAD_PATH:
# +        status, file = get_file(rubric_file_path)
# +        if status == FileStatus.BAD_PATH:
#              return {"message": f"File {rubric_file_path} not found in S3."}, 404
# -        elif status == fm.FileStatus.BAD_EXTENSION:
# +        elif status == FileStatus.BAD_EXTENSION:
#              return {"message": "File has an invalid extension."}, 400
# -        elif status == fm.FileStatus.UNKNOWN_ERR:
# +        elif status == FileStatus.UNKNOWN_ERR:
#              return {"message": "An unknown error occurred while retrieving the file from S3."}, 500
         
#          # Step 3: Load the outer JSON from the file-like object 
#          rubric_json = json.load(file)
#          # Step 4: Handle protential double encoding : to be done after confirming how things are stored in the file 
#          # Iterate over all key-value pairs in the JSON and ecode if the value is a string
# -        # for key, value in rubric_json.items(): 
# -        #         if isinstance(value, str):
# -        #                 # Try decoding the string into a proper JSON object
# -        #                 rubric_json[key] = json.loads(value)
# -        #         else:
# -        #             continue
# +        for key, value in rubric_json.items(): 
# +                if isinstance(value, str):
# +                        # Try decoding the string into a proper JSON object
# +                        rubric_json[key] = json.loads(value)
# +                else:
# +                    continue
#          # Return the full rubric JSON
#          return rubric_json, 200
#      except Exception as e:
# @@ -134,70 +134,56 @@ def update_rubric_changes(rubric_id, data):
 
#          # Step 2: Update the JSON data in S3
#          rubric_file_path = rubric.rubric_json_s3_file_path
# -        status, _ = fm.get_file(rubric_file_path)  # Check if the file exists in S3
# +        status, _ = get_file(rubric_file_path)  # Check if the file exists in S3
 
# -        if status == fm.FileStatus.BAD_PATH:
# +        if status == FileStatus.BAD_PATH:
#              return {"message": "Rubric file not found in S3."}, 404
# -        elif status != fm.FileStatus.OKAY:
# +        elif status != FileStatus.OKAY:
#              return {"message": "An unknown error occurred while retrieving the rubric file."}, 500
 
#          # Step 3: Replace the existing JSON in S3 with the new data
# -        status, message = fm.update_file_in_s3(rubric_file_path, json.dumps(data), 'application/json')
# +        status, message = update_file_in_s3(rubric_file_path, json.dumps(data), 'application/json')
 
#          if status != FileStatus.OKAY:
#              return {"message": f"Failed to update rubric in S3: {message}"}, 500
# -        # Step 4: Retrieve the updated rubric file from the s3 path
# -        rubric_file_path = rubric.rubric_json_s3_file_path
# -        # Use the get_file function to retrieve the file from s3
# -        status, file = fm.get_file(rubric_file_path)
# -        if status == fm.FileStatus.BAD_PATH:
# -            return {"message": f"File {rubric_file_path} not found in S3."}, 404
# -        elif status == fm.FileStatus.BAD_EXTENSION:
# -            return {"message": "File has an invalid extension."}, 400
# -        elif status == fm.FileStatus.UNKNOWN_ERR:
# -            return {"message": "An unknown error occurred while retrieving the file from S3."}, 500
# -        
# -        # Step 5: Load the outer JSON from the file-like object 
# -        rubric_json = json.load(file)
# -        return {"message": "Rubric updated successfully",
# -                "updated_rubric_json": rubric_json}, 200
# +
# +        return {"message": "Rubric updated successfully."}, 200
 
#      except Exception as e:
#          return {"message": f"An error occurred while updating the rubric {rubric_id}.", "error": str(e)}, 500
 
 
#  def delete_rubric_from_db(rubric_id):
# -
# +    try:
#          # Retrieve rubric
#          rubric = db.session.execute(select(RubricGenerated).filter_by(rubric_id=rubric_id)).scalar_one_or_none()
#          # If the rubric does not exist, return an error message
#          if rubric is None:
#              return {"message": "Rubric not found"}, 404
# -        filestatus = fm.del_file(rubric.rubric_json_s3_file_name)
# -        if filestatus != FileStatus.OKAY:
# -            return {"message": f"File {rubric.rubric_json_s3_file_name} could not be deleted", "error": filestatus.name}, 400
# -        else:
# -            db.session.delete(rubric)
# -        try:
# -            db.session.commit()
# -            return {"message" : f"File {rubric.rubric_json_s3_file_name} was deleted successfully"}, 200
# -        except Exception as e:
# -            db.session.rollback()
# -            return {"message": "An error occurred while deleting rubric file", "error": str(e)}, 500 
# +
# +        # Delete the rubric
# +        db.session.delete(rubric)
# +        db.session.commit()
# +        
# +        # Return a success message
# +        return {"message": "Rubric deleted successfully"}, 200
# +    except Exception as e:
# +        db.session.rollback()
# +        return {"message": "An error occurred while deleting the rubric.", "error": str(e)}, 500
 
#  def get_job_status(job_id):
#      try:
#          # Query the job status from the JobSubsystem
# -        job_status = js.get_job_status(job_id)  
# +        job_status = get_job_status(job_id)  
 
#          # Check if current job status
# -        if job_status == js.SubsystemStatus.COMPLETED_JOB:
# +        if job_status == SubsystemStatus.COMPLETED_JOB:
#              return {
#                  "message": "Rubric generation is completed.",
#                  "job_id": job_id,
#                  "status": "COMPLETED", 
#              }, 200
# -        elif job_status == js.SubsystemStatus.AWAITING_INSTANCE:
# +        elif job_status == SubsystemStatus.AWAITING_INSTANCE:
#              return {
#                  "message": "Rubric generation is in progress.",
#                  "job_id": job_id, 
# @@ -213,18 +199,18 @@ def get_job_status(job_id):
#              return {"message": "An error occurred while getting the status for {rubric_id}.", "error": str(e)}, 500
 
#  def download_rubric_as_pdf(rubric_id):
# -    pass
# -    # rubric = db.session.execute(select(RubricGenerated).filter_by(rubric_id=rubric_id)).scalar_one_or_none()
# +
# +    rubric = db.session.execute(select(RubricGenerated).filter_by(rubric_id=rubric_id)).scalar_one_or_none()
     
# -    # if rubric is None:
# -    #     return {"message": "Rubric not found"}, 404
# +    if rubric is None:
# +        return {"message": "Rubric not found"}, 404
     
# -    # rubric_pdf_file = fm.get_file(rubric.rubric_pdf_file_path)
# +    rubric_pdf_file = get_file(rubric.rubric_pdf_file_path)
 
# -    # try:
# -    #     return send_file(rubric_pdf_file , as_attachment=True), 200
# -    # except Exception as e:
# -    #     return {"message": f"An error occurred while downloading the generated rubric {rubric_id}", "error": str(e)}, 500
# +    try:
# +        return send_file(rubric_pdf_file , as_attachment=True), 200
# +    except Exception as e:
# +        return {"message": f"An error occurred while downloading the generated rubric {rubric_id}", "error": str(e)}, 500
     
#  def download_rubric_as_xlsx(rubric_id):
# -    pass
# +    pass
# \ No newline at end of file
# diff --git a/Backend/server/src/file_management.py b/Backend/server/src/file_management.py
# index 309190e..6c28f64 100644
# --- a/Backend/server/src/file_management.py
# +++ b/Backend/server/src/file_management.py
# @@ -181,7 +181,7 @@ def get_file(path: str) -> (FileStatus, io.StringIO):
 
#      except ClientError as e:
#          print(f"Failed to get object from S3: {e}")
# -        return FileStatus.UNKNOWN_ERR, None
# +        return FileStatus.ERROR, None
#          '''
         
#          file_content = response['Body'].read().decode('utf-8') # Decode bytes to string
# @@ -262,7 +262,7 @@ def download_file_from_s3(s3_path: str) -> FileStatus:
 
#      except ClientError as e:
#          print(f"Failed to download object from S3: {e}")
# -        return FileStatus.UNKNOWN_ERR, None
# +        return FileStatus.ERROR, None
     
#  def get_file_id(sID:int)->(FileStatus,_io.TextIOWrapper):
#      """Gets a file stored on disk by the ID used in databases, and returns a status code as well as a File obj."""
# @@ -271,7 +271,7 @@ def get_file_id(sID:int)->(FileStatus,_io.TextIOWrapper):
#      path = get_path(sID)
#      return get_file(path)
 
# -def create_file(name:str, data: dict, rename:bool = False)->(FileStatus ,str):
# +def create_file(name:str,rename:bool = False)->(FileStatus ,str):
#      """Creates a file in S3 and returns a status code as well as the file path in S3."""
#      if not _allowed_filename(name):
#          return FileStatus.BAD_EXTENSION, None, ''
# @@ -282,13 +282,11 @@ def create_file(name:str, data: dict, rename:bool = False)->(FileStatus ,str):
#      if rename:
#          name = _rename_for_duplicates(name)
#      # Create an empty file content
# -    file_content = json.dumps(data)
# +    file_content = ""
#      try:
#          # Upload the empty file to S3
#          s3.put_object(Bucket=S3_BUCKET_NAME, Key=name, Body=file_content, ContentType='application/json')
# -        # Construct the full file path
# -        file_path = f"s3://{S3_BUCKET_NAME}/{name}"
# -        return FileStatus.OKAY, file_path
# +        return FileStatus.OKAY, name
#      except Exception as e:
#          return(FileStatus.BAD_PATH, f"Error creating file in S3: {str(e)}")
# '''
# diff --git a/Backend/server/src/job_subsystem.py b/Backend/server/src/job_subsystem.py
# index be6c0b1..515368c 100644
# --- a/Backend/server/src/job_subsystem.py
# +++ b/Backend/server/src/job_subsystem.py
# @@ -83,7 +83,8 @@ class _SubsystemJob:
#      # Rubric specifics
#      projectOverview:str
#      staffEmail:str
# -    projectCriterions:[dict]
# +    projectCriterions:[str]
# +    targetSkills:dict
#      unitLearningOutcomes:[str]
 
#      # DEPRECATED: just use default jID and one of the create constructors
# @@ -150,8 +151,8 @@ class _SubsystemJob:
#      def create_rubric(self, params):
#          self.jobClass = _SubsystemJobType.RUBRIC
         
# -        self.jobID, self.projectOverview, self.staffEmail, \
# -                    self.projectCriterions, self.unitLearningOutcomes \
# +        self.jobID, self.unitName, self.unitLevel, self.projectName, self.projectOverview, self.staffEmail, self.projectCriterions, \
# +                    self.targetSkills, self.unitLearningOutcomes \
#                      = params
 
#      def equals(self, job):
# @@ -244,8 +245,12 @@ def _submit_job(job:_SubsystemJob)->(SubsystemStatus, str):
#              success,result = viva.regenerate_questions(input_data)
#      else:
#          input_data = {
# -            "assessment_description": job.projectOverview,
# +            "unit_name": job.unitName,
# +            "unit_level": job.unitLevel,
# +            "assessment_name": job.projectName,
# +            "assessment_overview": job.projectOverview,
#              "criteria": job.projectCriterions,
# +            "skills_per_criterion": job.targetSkills,
#              "ulos": job.unitLearningOutcomes
#              }
 
# @@ -262,19 +267,20 @@ def _process_completed_job(job:_SubsystemJob, data:dict)->SubsystemStatus:
     
#      combined_questions = qgenqueries.package_all_questions(job.submissionID, data)
#      name = job.projectName + '_generated_' + datetime.now().strftime("%d%m%Y_%H:%M:%S")
# -    status, s3_path = fm.create_file(name + '.json', combined_questions, rename=True)
# -    # filename = name + ".json"
# +    status, s3_path = fm.create_file(name + '.json', rename=True)
# +
#      if status != fm.FileStatus.OKAY:
#          return SubsystemStatus.FM_SYS_ERROR
# -    
# +
#      # Dump the JSON data to the S3 object
# -    # try:
# -    #     s3.put_object(Bucket=S3_BUCKET_NAME, Key=filename, Body=json.dumps(combined_questions), ContentType='application/json')
# -    # except ClientError as e:
# -    #     print(f"Error uploading JSON data to S3: {str(e)}")
# -    #     return SubsystemStatus.REMOTE_SYS_ERROR
# +    try:
# +        s3.put_object(Bucket=S3_BUCKET_NAME, Key=s3_path, Body=json.dumps(combined_questions), ContentType='application/json')
# +    except ClientError as e:
# +        print(f"Error uploading JSON data to S3: {str(e)}")
# +        return SubsystemStatus.REMOTE_SYS_ERROR
#      # json.dump(combined_questions, file) # This will have to be read back as json later
#      # file.close()
# +    
#      qgenqueries.upload_generated_files(job.submissionID, name, s3_path, 'GENERATED')
#      return SubsystemStatus.OKAY
 
# @@ -282,21 +288,18 @@ def _process_completed_rubric(job:_SubsystemJob, data:dict)->SubsystemStatus:
#      """Processes a completed rubric job, saving data and updating databases."""
 
#      name = job.projectName + '_rubric_' + datetime.now().strftime("%d%m%Y_%H:%M:%S")
# -    if data.get("rubric_title") is not None:
# -        name = data["rubric_title"]
# -    filename = name + ".json"
# -    status, s3_path = fm.create_file(name + '.json', data, rename=True)
# +    status, s3_path = fm.create_file(name + '.json', rename=True)
#      if status != fm.FileStatus.OKAY:
#          return SubsystemStatus.FM_SYS_ERROR
 
# -    # # Dump the JSON data to the S3 object
# -    # try:
# -    #     s3.put_object(Bucket=S3_BUCKET_NAME, Key=filename, Body=json.dumps(data), ContentType='application/json')
# -    # except ClientError as e:
# -    #     print(f"Error uploading JSON data to S3: {str(e)}")
# -    #     return SubsystemStatus.REMOTE_SYS_ERROR
# +    # Dump the JSON data to the S3 object
# +    try:
# +        s3.put_object(Bucket=S3_BUCKET_NAME, Key=s3_path, Body=json.dumps(combined_questions), ContentType='application/json')
# +    except ClientError as e:
# +        print(f"Error uploading JSON data to S3: {str(e)}")
# +        return SubsystemStatus.REMOTE_SYS_ERROR
#      idx = 201
# -    msg,idx = rgenqueries.upload_generated_rubric(job.staffEmail, name, filename, s3_path, "Generated")
# +    msg,idx = rgenqueries.upload_generated_rubric(job.staffEmail, job.projectName, name, s3_path)
 
#      if idx == 201:
#          return SubsystemStatus.OKAY
# @@ -380,6 +383,13 @@ def initialise(pollRate:float, instanceCount:int = 1, load:bool = False, s3_clie
#              aiKeys.get("OPENAI_PROJ_KEY")
#          )
 
# +    # TODO: add keys to .env file
# +    viva.init_openai(
# +        openai_api_key=os.getenv("OPENAI_API_KEY"),
# +        openai_org_key=os.getenv("OPENAI_ORG_KEY"),
# +        openai_proj_key=os.getenv("OPENAI_PROJ_KEY")
# +    )
# +
#      s3 = s3_client
#      S3_BUCKET_NAME = s3_bucket_name
     
# @@ -466,9 +476,13 @@ def submit_new_job(subID:int = 0,
 
#      return SubsystemStatus.OKAY, jID
 
# -def submit_new_rubric_job(staff_email:str,
# +def submit_new_rubric_job(unit:str,
# +                          level:str,
# +                          staff_email:str,
# +                          assessment_name:str,
#                            assessment_descript:str,
# -                          criterions:[dict],
# +                          criterions:[str],
# +                          skills:dict,
#                            ulos:[str])->(SubsystemStatus, int):
#      """Creates and submits a new rubric job."""
 
# @@ -481,7 +495,7 @@ def submit_new_rubric_job(staff_email:str,
#      _globalJobCounter += 1
 
#      job = _SubsystemJob(jID)
# -    params = [ jID, assessment_descript, staff_email, criterions, ulos ]
# +    params = [ jID, unit, level, staff_email, assessment_name, assessment_descript, criterions, skills, ulos ]
#      job.create_rubric(params)
 
#      if _doSingleThread:
# @@ -489,7 +503,7 @@ def submit_new_rubric_job(staff_email:str,
#          if status != SubsystemStatus.OKAY:
#              print(data)
#              return status, jID
# -        return _process_completed_rubric(job, json.loads(data)), jID
# +        return process_completed_rubric(job, data), jID
#      else:
#          _jobQueue.append(job)
 
# @@ -567,4 +581,4 @@ def create_job_from_json(json_data:str)->_SubsystemJob:
#          return None
#      job = _SubsystemJob(0, 0, '', 0, '', '', '', '')
#      job.deserialize(json_data)
# -    return job
# +    return job
# \ No newline at end of file
# diff --git a/import_and_stage_ai_files.bat b/import_and_stage_ai_files.bat
# index cd42d83..17e76b1 100644
# --- a/import_and_stage_ai_files.bat
# +++ b/import_and_stage_ai_files.bat
# @@ -14,7 +14,7 @@ cd ..
 
#  :: src files
#  :: "_internalRepo\AI\src\capote_ai\viva_questions.py"
# -:: "_internalRepo\AI\src\capote_ai\rubric_gen.py"
# +:: "_internalRepo\AI\src\capote_ai\rubric_template.py"
#  :: "_internalRepo\AI\src\capote_ai\pdf_to_text.py" 
#  :: dest folder
#  :: "Backend\server\src\ai"
