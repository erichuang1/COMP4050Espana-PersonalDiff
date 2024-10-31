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

$ScriptDescription = "This PowerShell script sets up the local Python virtual environment & Docker."

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
    cd ..\..\..
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
    echo "Setup (1/2): Please complete the initialisation process before using this flag."
    echo "Press any key to continue the initialisation process..."
    Read-Host
}

# Stage 2: Detect previous initialisation
cd (Split-Path $PSScriptRoot -Parent)
if (Test-Path -Path "env\installed") {
    # If so, skip initialisation
    cls
    echo "Setup (2/2): Setup found!"
} else {
    # If not, proceed Stage 2 initialisation process
    git update-index --assume-unchanged .\initialise_db.py
    git update-index --assume-unchanged .\docker-compose.yml
    git update-index --assume-unchanged .\cert.pem > $null 2>&1
    git update-index --assume-unchanged .\key.pem > $null 2>&1
    # To revert, use `git update-index --no-assume-unchanged file_path`
    python.exe -m pip install --upgrade pip
    pip install -r .\requirements.txt
    if (-not ((Test-Path -Path "cert.pem") -and (Test-Path -Path "key.pem"))) {
        python.exe .\generate_cert.py
    } else {
        echo "Existing cert.pem & key.pem found."
    }
    docker-compose build web
    docker-compose pull db
    docker-compose create
    New-Item -Path "env\installed" -ItemType "File"
    cls
    echo "Setup (2/2): Setup completed!"
}
echo "Run .\run-backend.ps1 again to start the local server."
