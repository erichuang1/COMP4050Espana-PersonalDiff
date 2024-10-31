# File Management
# by Harris C. McRae, 2024
#
# Initializes a process to manage uploading files.
# Stores the files somewhere on disk and then returns a simple path to find it.
# Should be called by an endpoint by passing the appropriate Request type.

import os.path
import os
import json
from enum import Enum
from flask import Flask, flash, request, redirect, url_for
from typing import Union
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from markdown_pdf import MarkdownPdf, Section
import _io
import boto3
from botocore.exceptions import ClientError
import io
from urllib.parse import urlparse
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
# _UPLOAD_FOLDER = 'file/'
_UPLOAD_FOLDER =  os.getenv('UPLOAD_FOLDER')
_EXTENSIONS = {'csv', 'pdf', 'md', 'json'}

# # Initialize S3 client
# s3 = boto3.client('s3')
# S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

class FileStatus(Enum):
    """A status code returned by functions in this file."""
    # Normal status codes
    OKAY = 0                    # All is well

    # Error codes
    BAD_PATH = -1               # A given path didn't lead to a file
    BAD_EXTENSION = -2          # The file held the wrong extension type
    NO_FILE = -3                # No file was uploaded
    WRONG_REQ = -4              # The given request was the wrong type of request
    ALREADY_EXIST = -5          # The file or file name already exists
    MALICIOUS_NAME = -6         # A delete has uncovered a malicious filename.
    UNKNOWN_ERR = -7            # Unknown S3 Related Error

def initialise(s3_client=None, s3_bucket_name=None)->FileStatus:
    """Initialises the file management system."""
    print("Initialising S3 file management system...")
    global s3, S3_BUCKET_NAME
        # Check if s3_client and s3_bucket are provided for S3 initialization
    if s3_client and s3_bucket_name:
        # Set global variables for S3 usage
        s3 = s3_client
        S3_BUCKET_NAME = s3_bucket_name
        print(f"S3 file management system initialised with bucket: {S3_BUCKET_NAME}")
        return FileStatus.OKAY
    else:     
        print("Error: Missing S3 client or bucket name.")
        print("S3_Client:" + str(s3_client))
        print("Bucket:" + str(s3_bucket_name))
        return FileStatus.BAD_PATH

def initialise_app(app:Flask, path:str = 'file/')->FileStatus:
    """Initialises the file management system. Configures the flask instance to put uploaded files in a default folder."""
    app.config['UPLOAD_FOLDER'] = path
    return initialise(path)

def _allowed_filename(filename:str)->bool:
    """Checks if a given filename is a valid filename (has the correct extension)"""
    # TODO: more comprehensive checks?
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in _EXTENSIONS

def _put_file_default_path(file:FileStorage, name:str)->str:
    """Uploads a given file to S3 under a filename and returns the path."""
    name = _rename_for_duplicates(name)
    try:
        s3.upload_fileobj(file, S3_BUCKET_NAME, name)
    except ClientError as e:
        # Handle specific AWS errors such as permission issues or missing credentials
        raise RuntimeError(f"Failed to upload to S3: {e.response['Error']['Message']}")
    except Exception as e:
        # Handle unexpected errors
        raise RuntimeError(f"An unexpected error occurred: {str(e)}")
    # Return the full S3 path
    return f"s3://{S3_BUCKET_NAME}/{name}"

def _rename_for_duplicates(name: str) -> str:
    """Creates a renamed file in the event that there are other files with the same name."""
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_objects_v2.html
    try:
        # Initial check for the given name
        objects = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=name)
        
        if 'Contents' not in objects:
            return name
        # Split the name into base and extension
        comps = name.rsplit('.', 1)
        i = 0
        # Generate a new name if the original name exists
        while True:
            new_name = f"{comps[0]}_{i}.{comps[1]}" if i > 0 else name
            # Check if the new_name exists in the bucket
            response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=new_name)
            if 'Contents' not in response or len(response['Contents']) == 0:
                return new_name  # Return the unique name if no such file exists
            i += 1
    except Exception as e:
        raise RuntimeError(f"Error checking for duplicates: {str(e)}")


def store_file_req(req:request) -> (FileStatus, str):
    """Parses a request for a file and returns a status code & the path it was stored at."""

    if req.method == 'GET':     # GET method: no file uploaded in request.
        return FileStatus.WRONG_REQ,str()
    
    if 'file' not in req.files: # No file uploaded.
        return FileStatus.NO_FILE,str()
    
    file = req.files['file']
    if file.filename == '':
        return FileStatus.NO_FILE,str()      # No file selected.

    if file:
        return store_file_storage(file)
    
    return FileStatus.NO_FILE,str()

def store_file_storage(file:FileStorage)->(FileStatus, str):
    """Stores a file and returns a status code, and the string path it was stored under."""
    if _allowed_filename(file.filename):
        filename = secure_filename(file.filename)
        path = _put_file_default_path(file, filename)
        return FileStatus.OKAY,path
    return FileStatus.BAD_EXTENSION,str()

def get_path(sID:int)->(FileStatus, str):
    """Returns the path of a given file based on its ID"""

    # TODO: integrate with database to get path from ID
    path = ''
    return path

def get_file(path: str) -> (FileStatus, io.StringIO):
    """Gets a file from S3 using the full S3 URI and returns a status code along with a file-like object.

    Parameters:
    path (str): The full S3 URI (e.g., 's3://bucket-name/path/to/file').

    Returns:
    FileStatus: Status of the file retrieval.
    io.StringIO: A file-like object containing the file content."""
    try:
    # Parse the S3 URI
        parsed_url = urlparse(path)
        key = parsed_url.path.lstrip('/')
        # Check if the file has a valid extension
        if not _allowed_filename(key):
            return FileStatus.BAD_EXTENSION, None
        # Check if the file has a valid extension
        if not _allowed_filename(key):
            return FileStatus.BAD_EXTENSION, None
        # Get the object from S3
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=key)

        # Read the file content as bytes (binary mode)
        file_content = response['Body'].read()
        print(f"File content type: {type(file_content)}")
        print(f"First 50 bytes of the file content: {file_content[:50]}")

        # Decode the binary content using 'cp1252'
        try:
            decoded_content = file_content.decode('cp1252')
            print("File content decoded successfully with 'cp1252'.")
        except UnicodeDecodeError:
            print("Failed to decode using 'cp1252'.")
            return FileStatus.OKAY, io.BytesIO(file_content)  # Return as binary data for further processing

        # If decoding is successful, return as a StringIO object
        file = io.StringIO(decoded_content)
        return FileStatus.OKAY, file

    except ClientError as e:
        print(f"Failed to get object from S3: {e}")
        return FileStatus.UNKNOWN_ERR, None
        '''
        
        file_content = response['Body'].read().decode('utf-8') # Decode bytes to string
        file = io.StringIO(file_content) # Create a StringIO object for text processing
        return FileStatus.OKAY, file
    except ClientError as e:
        # Check if the error is due to the file not being found
        if e.response['Error']['Code'] == 'NoSuchKey':
            return FileStatus.BAD_PATH, None
        else:
            print(f"Error retrieving file from S3: {str(e)}")
            return FileStatus.UNKNOWN_ERR, None
        '''
import io
import boto3
from botocore.exceptions import ClientError
from urllib.parse import urlparse

s3 = boto3.client('s3')
S3_BUCKET_NAME = 'your-bucket-name'

def get_pdf_binary_file(path: str) -> (FileStatus, io.BytesIO):
    """
    Gets a file from S3 using the full S3 URI and returns a status code along with a file-like object.

    Parameters:
    path (str): The full S3 URI (e.g., 's3://bucket-name/path/to/file').

    Returns:
    FileStatus: Status of the file retrieval.
    io.BytesIO: A file-like object containing the file content in binary.
    """
    try:
        # Parse the S3 URI
        parsed_url = urlparse(path)
        key = parsed_url.path.lstrip('/')

        # Get the object from S3
        response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=key)

        # Read the file content as bytes (binary mode)
        file_content = response['Body'].read()

        # Return as a BytesIO object
        return FileStatus.OKAY, io.BytesIO(file_content)

    except ClientError as e:
        print(f"Failed to get object from S3: {e}")
        return FileStatus.ERROR, None
    
def download_file_from_s3(s3_path: str) -> FileStatus:
    """
    Downloads a file from S3 using the full S3 URI and saves it to the UPLOAD_FOLDER.

    Parameters:
    s3_path (str): The full S3 URI (e.g., 's3://bucket-name/path/to/file').
    local_filename (str): The name of the file to save in the UPLOAD_FOLDER.

    Returns:
    FileStatus: Status of the file download.
    """
    try:
        # Ensure the UPLOAD_FOLDER exists
        if not os.path.exists(_UPLOAD_FOLDER):
            os.makedirs(_UPLOAD_FOLDER)

        # Parse the S3 URI
        parsed_url = urlparse(s3_path)
        key = parsed_url.path.lstrip('/')

        # Extract the file name from the key
        file_name = os.path.basename(key)
        local_file_path = os.path.join(_UPLOAD_FOLDER, file_name)
        # Download the file from S3 to the specified local path
        s3.download_file(S3_BUCKET_NAME, key, local_file_path)

        return FileStatus.OKAY, local_file_path  # Return the status and the file path

    except ClientError as e:
        print(f"Failed to download object from S3: {e}")
        return FileStatus.UNKNOWN_ERR, None
    
def get_file_id(sID:int)->(FileStatus,_io.TextIOWrapper):
    """Gets a file stored on disk by the ID used in databases, and returns a status code as well as a File obj."""

    # TODO: get the path from databases and search for it.
    path = get_path(sID)
    return get_file(path)

def create_json_file(name:str, data: dict, rename:bool = False)->(FileStatus ,str):
    """Creates a file in S3 using the name passed in as parameter
        And dumps the dict passed in as parameter as file content 
        and returns a status code as well as the file path in S3."""
    if not _allowed_filename(name):
        return FileStatus.BAD_EXTENSION, None

    # Sanitize the file name
    name = secure_filename(name)
    # Check if file exists in S3
    if rename:
        name = _rename_for_duplicates(name)
    # Create an empty file content
    file_content = json.dumps(data)
    try: 
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=name, Body=file_content, ContentType='application/json')
        # Construct the full file path
        file_path = f"s3://{S3_BUCKET_NAME}/{name}"
        return FileStatus.OKAY, file_path
    except Exception as e:
        return(FileStatus.BAD_PATH, f"Error creating file in S3: {str(e)}"), None

# Plain text version for testing
def create_md_file(name:str, data: str, rename:bool = False)->(FileStatus ,str):
    """Creates a file in S3 and returns a status code as well as the file path in S3."""
    if not _allowed_filename(name):
        return FileStatus.BAD_EXTENSION, None
    
    # Sanitize the file name
    name = secure_filename(name)
    # Check if file exists in S3
    if rename:
        name = _rename_for_duplicates(name)
    try:
    # Upload the empty file to S3
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=name, Body=data, ContentType='application/json')
        # Construct the full file path
        file_path = f"s3://{S3_BUCKET_NAME}/{name}"
        return FileStatus.OKAY, file_path
    except Exception as e:
        return(FileStatus.BAD_PATH, f"Error creating file in S3: {str(e)}"), None
    
def del_file(name:str)->FileStatus:
    """Deletes a file from the S3 bucket."""
    if not _allowed_filename(name):
        return FileStatus.BAD_EXTENSION
    
    name = secure_filename(name)

    try:
        # Attempt to delete the object from S3
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=name)
        return FileStatus.OKAY
    except ClientError as e:
        # Check if the error is due to the file not being found
        if e.response['Error']['Code'] == 'NoSuchKey':
            return FileStatus.NO_FILE
        else:
            print(f"Error deleting file from S3: {str(e)}")
            return FileStatus.UNKNOWN_ERR
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return FileStatus.UNKNOWN_ERR

def clear_folder() -> FileStatus:
    """
    Deletes all files in the S3 bucket.

    :return: FileStatus indicating success or failure.
    """
    global s3, S3_BUCKET_NAME

    try:
        # Paginator to handle cases with many objects
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET_NAME)

        objects_to_delete = []

        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects_to_delete.append({'Key': obj['Key']})

        if objects_to_delete:
            # Delete all objects in the list
            delete_response = s3.delete_objects(
                Bucket=S3_BUCKET_NAME,
                Delete={'Objects': objects_to_delete}
            )

            # Check for errors in the delete response
            if 'Errors' in delete_response:
                print(f"Errors occurred while deleting objects: {delete_response['Errors']}")
                return FileStatus.UNKNOWN_ERR

        return FileStatus.OKAY

    except ClientError as e:
        print(f"Error clearing S3 bucket: {str(e)}")
        return FileStatus.UNKNOWN_ERR
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return FileStatus.UNKNOWN_ERR

def convert_md_to_pdf(path:str, target_local = False)->(FileStatus, str):
    """Converts a MD file to a PDF file and stores it under the same name with a .pdf extension."""
    if not target_local:
        status,file = get_file(path)
        if status != FileStatus.OKAY:
            return status, ''
    else:
        file = open(path, 'rt')

    outpath = path.rsplit('.',1)[0]
    outpath = outpath + '.pdf'
    exten = path.rsplit('.',1)[1].lower()
    if exten != 'md':
        return FileStatus.BAD_EXTENSION,''
    
    content:str = ''

    for line in file:
        content += line

    if target_local:
        file.close()
    
    return convert_md_str_to_pdf(content, outpath)

def convert_md_str_to_pdf(data:str, path:str)->(FileStatus, str):
    """Converts a given MD formatted string into a PDF file and stores it in the output file path."""
    
    exten = path.rsplit('.',1)[1].lower()
    if exten != 'pdf':
        return FileStatus.BAD_EXTENSION,''
    
    pdf = MarkdownPdf(toc_level = 3)
    pdf.meta['title'] = 'Title'
        
    pdf.add_section(Section(data, toc=False))

    pdf.save(path)
    return FileStatus.OKAY,path

def convert_md_str_to_pdf_bytes(data:str)->(FileStatus, io.BytesIO):
    """Converts a given MD formatted string into a PDF format and returns a BytesIO object for that PDF format."""
    pdf = MarkdownPdf(toc_level = 3)
    pdf.meta['title'] = 'Title'
    pdf_bytes = io.BytesIO()
    pdf.add_section(Section(data, toc=False))

    pdf.save(pdf_bytes)
    pdf_bytes.seek(0)
    return FileStatus.OKAY,pdf_bytes

def update_file_in_s3(file_path: str, new_content: str, content_type: str) -> (FileStatus, str):
    """
    Updates the content of an existing file in S3 using `put_object`.
    
    :param file_path: The S3 URI of the file to update (e.g., 's3://bucket-name/path/to/file').
    :param new_content: The new content to write into the file (as a string).
    :param content_type: The MIME type of the file content (default: application/json).
    :return: A tuple containing a FileStatus indicating success or failure and a message.
    """
    try:
        # Parse the S3 URI to extract the bucket and key
        parsed_url = urlparse(file_path)
        bucket = parsed_url.netloc
        key = parsed_url.path.lstrip('/')  # Remove the leading '/' from the key
        
        # Check if the file has a valid extension before updating
        if not _allowed_filename(key):
            return FileStatus.BAD_EXTENSION, "Invalid file extension."

        # Overwrite the file with new content in S3
        s3.put_object(Bucket=bucket, Key=key, Body=new_content, ContentType=content_type)

        return FileStatus.OKAY, "File updated successfully."
    except ClientError as e:
        # Handle specific AWS errors, such as permission issues or missing credentials
        error_message = f"Error updating file in S3: {e.response['Error']['Message']}"
        return FileStatus.UNKNOWN_ERR, error_message
    except Exception as e:
        # Handle unexpected errors
        error_message = f"An unexpected error occurred: {str(e)}"
        return FileStatus.UNKNOWN_ERR, error_message
