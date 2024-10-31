##THIS IS A TEST CLIENT FOR TESTING OUR API THROUGH EXAMPLE REQUESTS THAT WILL BE MADE BY BACKEND

import requests

#url = "http://127.0.0.1:5000/generatequestions" #For Local - use this when running API locally
url = "https://comp4050espana.onrender.com/generatequestions" #For Render

FILE_PATH = 'COMP4050_Sample_Assignment.pdf'

# Data to be sent along with the file
data = {
    "job_id" : 1,
    "assignment_title": "Impact of Agile Methodologies on Software Development",
    "unit_name": "Introduction to Software Engineering",
    "no_of_questions":"" ,
    "question_challenging_level": "Medium"
}

# The PDF file to be uploaded
files = {
    'file': ('assignment.pdf', open(FILE_PATH, 'rb'), 'application/pdf')
}

# Send the POST request as a multipart request. 
# data = data represents the user selected parameters as defined in data{}
# files=files represents the actual assignemnt PDF file 
response = requests.post(url, data=data, files=files)

# Print the response
print(response.json())

