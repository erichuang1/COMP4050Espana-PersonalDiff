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

$ScriptDescription = "This PowerShell script starts the local server."

# A python cli handler that can indicate running state
Set-Alias -Name py -Value Run-PythonScript
function Run-PythonScript {
    # Example usage:
    # Run-PythonScript -ScriptPath ".\initialise_db.py" -Args @("arg1", "arg2")
    param (
        [Parameter(Mandatory=$true, Position=0)]
        [string]$ScriptPath,
        
        [Parameter(Position=1)]
        [string[]]$Args
    )
    
    $argString = $Args -join ' '
    $command = "python $ScriptPath $argString"
    echo "Executing ""$ScriptPath""..."
    Invoke-Expression $command
    echo "Finished script, exiting..."
}

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
    cd ..\..
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

# PyTest: Rubric Download
if ($t) {
    pytest .\src\tests\test_rubrics.py
    exit
}


cls
echo "For CLI cheatsheet & help message, run:"
echo "  .\run-backend.ps1 -h"
echo "=================================================="

# Generate self-signed certificate for HTTPS
if ($g) {
    python.exe .\generate_cert.py
}


# Run Local Server / Docker
if ($d) {
    if (Test-Path -Path ".env.docker") {
        ren ".env" ".env.local"
        ren ".env.docker" ".env"
    }
    docker-compose up
} else {
    if (Test-Path -Path ".env.local") {
        ren ".env" ".env.docker"
        ren ".env.local" ".env"
    }
    docker-compose up db -d
    # Database: Initialise
    if ($i) {
        py .\initialise_db.py
    }
    py .\run.py
}
