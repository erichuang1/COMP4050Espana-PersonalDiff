import requests

# Set the URL for your Flask server
url = "http://localhost:5000/regeneratequestions"

# File you want to upload 
FILE_PATH = 'COMP4050_Sample_Assignment.pdf'

# Data to be sent in the request (including questions and reasons as key-value pairs)
data = {
    "job_id": "2",  # Example job_id
    "assignment_title": "Impact of Agile Methodologies on Software Development",
    "unit_name": "Introduction to Software Engineering",
    "question_reason[]": [
        {"question": "What are the core principles of Agile?", "reason": "Too vague"},
        {"question": "How does Scrum framework work?", "reason": "Not detailed enough"}
    ]
}

# Prepare the file upload
files = {
    'file': open(FILE_PATH, 'rb')
}

# Send POST request to Flask API
response = requests.post(url, data=data, files=files)

# Print the response
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
