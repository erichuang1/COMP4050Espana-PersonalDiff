param (
    [switch]$h,
    [switch]$r,
    [switch]$g,
    [switch]$i,
    [switch]$id,
    [switch]$d,
    [switch]$a,
    [switch]$sql,
    [switch]$t
)

$ScriptDescription = "This PowerShell script check, initialise, and activates the Python virtual environment."

# Help message
if ($h) {
    echo "CLI Cheatsheet"
    echo ""
    echo "Python: Freeze Requirements   pip freeze > requirements.txt"
    echo "Flask: Run Local Server       flask run --debug --host=0.0.0.0 --port=443"
    echo "Docker: Start Container       docker-compose up --build"
    echo "Docker: Detach Container      Ctrl+Shift+P -> Terminal: Detach Session"
    echo "Docker: Attach Container      docker attach flask_container"
    echo "Docker: DB Initialise         docker exec -it flask_container python initialise_db.py"
    echo "Docker: Connect DB            docker exec -it mysql_container mysql -u root -ppasswordtest123"
    echo "SQL: Switch to DB             use 4050Backend;"
    echo "SQL: List All Tables          show full tables;"
    echo "SQL: View Table               select * from <table>;"
    echo "PyTest: Rubric Download       pytest .\src\tests\test_rubrics.py"
    echo "=================================================="
    echo "$ScriptDescription"
    echo ""
    echo ".\run-backend.ps1 [-h]|[-r]|[-a]|[-sql]"
    echo "              ... [-g] [-i]"
    echo ""
    echo "  -h   Display this help message"
    echo "  -r   Re-initialise setup"
    echo "  -g   Generate self-signed certificate for HTTPS"
    echo "  -i   Database: Initialise"
    echo "  -id  Docker: Initialise Database"
    echo "  -d   Docker: Run Docker instead"
    echo "  -a   Docker: Terminal attach flask_container"
    echo "  -sql Docker: Terminal connect database"
    echo "  -t   PyTest: Rubric Download"
    echo ""
    exit
}

# Re-initialise setup
cd $PSScriptRoot
if ($r) {
    Remove-Item -Path "$PSScriptRoot\env\installed" -Force -ErrorAction SilentlyContinue
    .\run-backend.ps1
    exit
}

# Docker: Initialise Database
if ($id) {
    docker exec -it flask_container python initialise_db.py
    exit
}

# Docker: Terminal attach flask_container
if ($a) {
    cls
    docker attach flask_container
    exit
}

# Docker: Terminal connect database
if ($sql) {
    docker exec -it mysql_container mysql -u root -ppasswordtest123
    exit
}

# Flags that are requring the initialisation process
if ($g -or $i -or $t -or $d) {
    echo "Setup (0/2): Please complete the initialisation process before using this flag."
    echo "Press any key to start the initialisation process..."
    Read-Host
}

# .env check
if (-not (Test-Path -Path "Backend\server\.env")) {
    echo "Please setup .env before running (See README.md for more info)."
    exit
}

# Stage 1: Python venv setup
cd $PSScriptRoot\Backend\server
if (-not (Test-Path -Path "env")) {
    echo "Creating Python virtual environment..."
    python -m venv env
    echo "Completed!"
}
cls

# Stage 1: Detect previous initialisation
echo "Initiating setup..."
if (Test-Path -Path "env\installed") {
    # If so, skip initialisation
    echo "Setup: Setup found!"
    echo "Activating Python Virtual Environment..."
    echo "Run .\run-backend.ps1 again to start the server."
    .\setup-script\activate-venv.ps1
} else {
    # If not, proceed to Stage 2 initialisation process
    cd $PSScriptRoot\Backend\server\setup-script
    echo "Setup (1/2): Run .\run-backend.ps1 again to complete the setup."
    echo "Activating Python Virtual Environment..."
    .\activate-venv.ps1
}
