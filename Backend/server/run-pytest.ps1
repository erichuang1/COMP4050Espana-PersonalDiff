# This PowerShell script is for running pytests

cls
echo "PyTest Rubric Download:       pytest .\src\tests\test_rubrics.py"
echo "Docker DB Initialise:         docker exec -it flask_container python initialise_db.py"
echo "Docker DB Connect:            docker exec -it mysql_container mysql -u root -p"
pytest .\src\tests\test_rubrics.py