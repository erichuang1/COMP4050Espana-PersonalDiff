# Question Generation:
1. For each submission, the AI module sends Backend's job system module the questions generated in JSON format
2. The questions for that particular submission is stored as a ".json" file in the disk using the file management system 
   1. Then the file management system calls the `upload_generated_files(submission_id, generated_file_name, generated_file_path, status) helper method, so that the info passed in can be stored in the DB
3. Backend endpoint will send the frontend the questions generated for each submission as `json` as well
   1. That way frontend can display the questions in separate questions, rather than a pdf file
4. But if a user wants to download the Generated question file as pdf, we can parse the json file to a pdf file and send it over to frontend
   1. Then frontend can render as pdf/allow the user to download


# Initialisation of job_subsystem and file_system
- To be done in `main.py`
- Did not work, causing infinite loop/deadlock in the ec2 instance 


# Merge endpoint branch with BackendBranch 


# Test csv upload with postman

# Test units and projects with new model and new endpoints

# Pull changes from BackendBranch into BackendTesting