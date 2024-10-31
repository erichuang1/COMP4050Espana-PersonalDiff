## 1. Introduction
   - TODO

## 2. Project Structure
   - The project is organised into different directories and modules to make the codebase easier to manage. Below is an overview of all the folders.
      ```bash 
      src/
      ├── ai/
      ├── controllers/ 
      ├── models/
      ├── routes/
      ├── templates/
      ├── tests/
      ├── __init__.py
      ├── db_instance.py
      ├── file_management.py
      ├── formatting.py
      ├── job_subsystem.py
      ├── main.py
      ├── run.py
      └── initialise_db.py
      ```
   - `ai/` : Handles the logic for ai-related tasks. The module is invoked by job_subsytem.
   - `controllers/` : This folder contains files, that contain the logic to interact with the model based on the route.
   - `models/` : 
   - `routes/` : Defined the endpoints of the application. Each route connects to specific controllers for executing logic when users interact with the web app.
   - `tests/`: Contains unit tests. This is where tests can be defined for different modules of to ensure the application functions as expected.
   - `db_instance.py` : This file sets up and configures the database instance using SQLAlchemy.
   - `file_management.py` : This file handles all file-related operations within the project, particularly focusing on interactions with aws S3.
   - `job_subsystem.py` : This file handles the logic for task scheduling and execution.Also interacts with the ai module. 
   - `formatting.py` : Contains helper functions for formatting data or transforming output.
   - `initialise_db.py`: This file is used to initialise and set up the database for the application. Used to create the necessary database tables and insert initial or test data into the database. 
   - `main.py`: The entry point for running the application. Initializes the app and defines the main functions.
   - `run.py`: Script to start server.

## 3. Setting Up the Development Environment
   - TODO


## 4. Running the Project Locally
### Windows
```bash
cd Backend\server

# Untrack changes for the following files
git update-index --assume-unchanged .\initialise_db.py
git update-index --assume-unchanged .\docker-compose.yml

# Setup Python environment
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
```
Alternatively, you can use `run-backend.ps1` to simplify the setup process. You may need to [adjust your PowerShell script execution settings](https://superuser.com/questions/106360/how-to-enable-execution-of-powershell-scripts), or in other cases, zip & unzip the repo to remove the download protection tags. 

### macOS
```bash
cd Backend\server

# Untrack changes for the following files
git update-index --assume-unchanged /initialise_db.py
git update-index --assume-unchanged /docker-compose.yml

# Setup Python environment
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Prerequisites

Before running the project, ensure the following are installed:

- [Docker Desktop](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (On Windows, available automatically when Docker Desktop is installed)
- [CURL](https://curl.se/download.html) (for sending requests via the command line, built-in within Windows)


# Step 2 - Preparing the `.env` Configuration File:
1. Install Docker on your local machine 
2. Review the `docker-compose.yml` and `Dockerfile` 
   1. In the `docker-compose.yml`, add path for location where you need to save files. (This is the volumes for web)
   2. The command `build .` in the `Dockerfile` means the image for the Flask container will be built using the `Dockerfile` in the current directory
3. Create a .env file in the root directory (inside `server`) (ensure this file is added to your .gitignore to avoid pushing sensitive information to GitHub).

```bash
MYSQL_ROOT_PASSWORD=rootpasswd123
MYSQL_DATABASE=4050Backend
MYSQL_USER=testUser
MYSQL_PASSWORD=testUser123
SQLALCHEMY_DATABASE_URI='mysql+pymysql://testUser:testUser123@mysql_container:3306/4050Backend'
CLIENT_ID=<client id>
CLIENT_SECRET=<client secret>
OPENAI_API_KEY=<addyourkey>
AWS_ACCESS_KEY_ID=<your_access_key_id>
AWS_SECRET_ACCESS_KEY=<your_secret_access_key>
AWS_DEFAULT_REGION=ap-southeast-2
S3_BUCKET_NAME=4050bucket
# Service keys are requried for the server to function properlly
```

## Setup services and get revelant keys
### Steps to create OpenAPIKey

1. Go to [OpenAI Platform](https://platform.openai.com/playground/chat?models=o1-mini)
2. Login or Sign-up
3. Click on `Dashboard` 
4. Select `API Keys` -> `Create new secret key`
5. Add the secret key to `.env`

### Steps to create IAM User on AWS

1. Go to [AWS Management Console](https://aws.amazon.com/console/)
2. Create new account or sign in using `root user`
3. Go to IAM Dashborad and click on Users in the left navigation pane.
4. Click the Add user button.
5. Enter a User name (e.g., 4050-app-user).
6. Click on `Provide user access to the AWS Management Console` - optional
7. Select the option `I want to create an IAM user`
8. In the section console password, click on `Custom password` (set the password)
10. Under Select AWS credential type, check Access key - Programmatic access.
11. Click Next: Permissions-> `Set Boundary Permissions`
12. Set Permissions for the User : Choose a policy like `AmazonS3FullAccess`
13. Review the information and click Create user.
14. Once the IAM User is created, click on the user
15. Under the summary Tab, click create access key
16. Select the option `Local Code`
17. Once the access key and secret key is created
18. Add to the `.env` file

### Steps to create a S3 bucket 

1. Login to [AWS Management Console](https://aws.amazon.com/console/)
2. Search S3 in search bar
3. Click `create bucket`
4. The bucket name should be : `4050bucket` (same as what is specified in the `.env`)
5. Under the Default Encryption Tab -> Bucket key -> select `Disable`
6. Click `create bucket`.


### Steps to configue AWS 
Instructions on AWS website : [Instructions](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

The following instruction For macOS : 

1. Download the installer from the official AWS website or use the command line:
   ```bash
      curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
   ```
2. Install the AWS CLI:
   Once downloaded, install the package using the following command:
   ```bash
      sudo installer -pkg AWSCLIV2.pkg -target /
   ```
3. Verify the Installation:
   ```bash
      aws --version
   ``` 
4. After installing the AWS CLI, run the following command to configure it:
   ```bash
      aws configure
   ```
5. Enter the Required Information 
   ```bash 
      AWS Access Key ID [None]: your_access_key_id
      AWS Secret Access Key [None]: your_secret_access_key
      Default region name [None]: ap-southeast-2
      Default output format [None]: json
   ```
6. Test the configuration by listing your S3 buckets
   ```bash
      aws s3 ls
   ```

#### Interacting S3 with Command Lines: 
To check list of s3 bucket :

```bash
   aws s3 ls
```

To check the files in s3 bucket :

```bash
   aws s3 ls s3://4050bucket/
```

To delete a file in s3 bucket :

```bash
   aws s3 rm s3://4050bucket/file-name-.pdf
```
## Notes regarding the Database
1. `pymysql` in the URI is the connector that allows `SQLAlchemy` to interface with the MySQL database so it can convert the `SQLAlchemy` models/python classes in `\src\models\models_all.py` into SQL tables in the mysql database running in the MySQL container.
   1. `models\__init__.py` allows us to import all the models at once, just by importing the folder `models` in `initialise_db.py` to get access to every model

## Notes regarding the Docker images
**1. Flask Server Container**
- The image for the Flask server container is built from the `Dockerfile` located in the `server `directory.
**2. MySQL Database Container**
- The MySQL database container uses a precompiled `mysql` image specified in the `docker-compose.yml`.
- The docker-compose.yml file separates the two containers (`flask_container` and `mysql_container`) into distinct services (`web` and `db`) and ensures that the Flask container is dependent on the MySQL container.
- It also sets up networking so the containers can communicate with each other.


# Step 3 - Commands to run after setting up .env file:
## If you are running the server in Docker
1. Make sure `SQLALCHEMY_DATABASE_URI` uses port `3306`. 
2. `docker-compose build` builds the image from the Dockerfile and the precompiled mysql image
3. `docker-compose up` starts the docker containers or `docker-compose up --build`
4. `docker exec -it flask_container python initialise_db.py` to initialise the MySQL database and create tables in the database using the `SQLAlchemy` Models in `models_all.py`. 
5. `docker exec -it flask_container python generate_cert.py` to generate or renew the self-signed HTTPS certificate. 
6. After that, you will be able to go to `Docker Desktop` and see both the containers running
7. You can access your localhost at port `80` or `443` to access the active flask server
8. To enter terminal of the `mysql_container` do the following:
   1. `docker exec -it mysql_container bash`
9. To interact with the database itself do
   1. `mysql -u testUser -p`
   2. Enter the password you set for your database : `testUer123`
   3. `use 4050Backend` to able to write quieries for the tables in that database 
   4. `describe unit;` to see all the columns and datatypes in the `unit` table.

## If you want to run the Flask Server Locally
1. Make sure `SQLALCHEMY_DATABASE_URI` uses port `3307`. 
2. Open `.env` file, modify `SQLALCHEMY_DATABASE_URI` to have `@localhost` instead, like this: 
   ```bash
   SQLALCHEMY_DATABASE_URI='mysql+pymysql://testUser:testUser123@localhost:3306/4050Backend'
   ```
3. `docker-compose build` builds the image from the Dockerfile and the precompiled mysql image
4. `docker-compose up mysql_container` to start the database server.
5. `python initialise_db.py` to initialise the MySQL database. 
   1. Refer to the diagnostics section if you encountered an error during this step.
6. `python generate_cert.py` to generate or renew the self-signed HTTPS certificate. 
7. Optional: To interact with the database, do
   1. `docker exec -it mysql_container mysql -u root -ppasswordtest123`
   2. `use 4050Backend;` to switch to our database
   3. `show full tables;` to list all tables
   4. `select * from <table>;` to view table content
   5. `describe unit;` to view table properties.

## If you encountered errors in `initialise_db.py`:
### Error 1: Port Not Open
Example error message: 
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server on 'localhost' ([WinError 10061] No connection could be made because the target machine actively refused it)")
```
Resolution: In `SQLALCHEMY_DATABASE_URI`, replace `<port>` with either `3306` or `3307` depending where you are running the server (`3306` for docker, `3307` for local):
```bash
SQLALCHEMY_DATABASE_URI='mysql+pymysql://testUser:testUser123@localhost:<port>/4050Backend'
```
On Windows, you could also try restarting its Network Address Translation (NAT) Service to release the ports being used:
```bash
net stop winnat
net start winnat
```

### Error 2: DB User Not Initialised
Example error message: 
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (1045, "Access denied for user 'testuser'@'172.18.0.1' (using password: YES)")
```
Resolution: Access mysql using one of the following methods:
- `docker exec -it mysql_container mysql -u root -ppasswordtest123`
- Open Docker Desktop, nevigate to `mysql_container`, in the Exec tab, run `mysql -u root -ppasswordtest123`

Now execute all commands in `init.sql` to manually initialise the users. 

Note: There were cases that a restart of the computer is needed to solve this issue. 

### Error 3: DNS Name Not Resolved
Example error message: 
```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server on 'mysql_container' ([Errno 11001] getaddrinfo failed)")
````
Resolution: In `SQLALCHEMY_DATABASE_URI`, replace `<addr_name>` with either `localhost` or `mysql_container` depending where you are running the server:
```bash
SQLALCHEMY_DATABASE_URI='mysql+pymysql://testUser:testUser123@<addr_name>:3306/4050Backend'
```

### If you are using `run-backend.ps1`
You can create a second .env file (e.g. `.env.docker` or `.env.local`). The script will recognise them and switch automatically depending on the mode selected. (e.g. `.\run-backend.ps1 -d` will switch to the docker config.) 


# Step 4 - To test the server using command line:

-  Run the following command (replace `<address>` with the server address):
   ```bash
   curl -X GET http://<address>/units/CS101 
   ```

- The output should be like
   ```
      {
         "convener_id": 1,
         "level": "First Year",
         "session": "S1",
         "unit_code": "CS101",
         "unit_name": "Intro to Computer Science",
         "year": 2024
         }
   ```
