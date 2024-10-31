# This PowerShell script check, initialise, and activates the Python virtual environment

# Use the switch -r to reinitiate the setup
param (
    [switch]$r,
    [switch]$h
)

if ($h) {
    echo "This PowerShell script check, initialise, and activates the Python virtual environment."
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
    .\run-backend.ps1
    exit
}

cd $PSScriptRoot\Backend\server
if (-not (Test-Path -Path "env")) {
    echo "Creating Python virtual environment..."
    python -m venv env
    echo "Completed!"
}
cls
echo "Initiating setup..."
if (Test-Path -Path "env\installed") {
    echo "Setup: Setup found!"
    echo "Activating Python Virtual Environment..."
    echo "Run .\run-backend.ps1 again to start the server. "
    .\setup-script\activate-venv.ps1
} else {
    cd $PSScriptRoot\Backend\server\setup-script
    echo "Setup (1/2): Run .\run-backend.ps1 again to complete the setup. "
    echo "Remember to setup .env before running. (See README.md for more info.) "
    echo "Activating Python Virtual Environment..."
    .\activate-venv.ps1
}
