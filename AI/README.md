
This document details how to setup the AI component on your PC.

1. Create an .env file and add the following:
```.env
OPENAI_API_KEY = ******************************
organization = **************
project = ***************
```
2. Setup a virtual environment using the following command:
```powershell
py -3.12 -m venv venv_name
```
3. Activate the virtual environment:
```powershell
.\venv_name\Scripts\activate
```
4. Install all requirements using pip:
```powershell
pip install -r .\requirements.txt
```
