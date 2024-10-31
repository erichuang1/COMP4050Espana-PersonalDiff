# This PowerShell script starts the server

# Use the switch -r to reinitiate the setup
param (
    [switch]$r,
    [switch]$h
)

if ($h) {
    echo "This PowerShell script starts the server."
    echo ""
    echo ".\run-backend.ps1 [-h]|[-r]"
    echo ""
    echo "  -h  Display this help message"
    echo "  -r  Re-initialise setup"
    echo ""
    exit
}

cd $PSScriptRoot
if ($r) {
    Remove-Item -Path "$PSScriptRoot\env\installed" -Force -ErrorAction SilentlyContinue
    cd ..\..
    .\run-backend.ps1
    exit
}


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
    echo "Executing $ScriptPath"
    echo "Python is loading..."
    Invoke-Expression $command
    echo "Finished script, exiting..."
}

cls
echo "Python Freeze Requirements:   pip freeze > requirements.txt"
echo "Flask Run Local Server:       flask run --debug --host=localhost --port=80"
echo "Docker Start Container:       docker-compose up --build"
echo "Docker Detach Container:      Ctrl+Shift+P -> Terminal: Detach Session"
echo "Docker Attach Container:      docker attach flask_container"
echo "Docker DB Initialise:         docker exec -it flask_container python initialise_db.py"
echo "Docker DB Connect:            docker exec -it mysql_container mysql -u root -p"
echo "=================================================="
# docker-compose up
py .\initialise_db.py
py .\run.py
# py .\generate_cert.py