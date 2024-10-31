# This PowerShell script sets up the local Python virtual environment & Docker

# Use the switch -r to reinitiate the setup
param (
    [switch]$r,
    [switch]$h
)

if ($h) {
    echo "This PowerShell script sets up the local Python virtual environment & Docker."
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
    cd ..\..\..
    .\run-backend.ps1
    exit
}

cd (Split-Path $PSScriptRoot -Parent)
if (Test-Path -Path "env\installed") {
    cls
    echo "Setup (2/2): Setup found!"
} else {
    git update-index --assume-unchanged .\initialise_db.py
    git update-index --assume-unchanged .\docker-compose.yml
    python.exe -m pip install --upgrade pip
    pip install -r .\requirements.txt
    docker-compose build
    New-Item -Path "env\installed" -ItemType "File"
    cls
    echo "Setup (2/2): Setup completed!"
}
echo "Run .\run-backend.ps1 again to start the server. "
