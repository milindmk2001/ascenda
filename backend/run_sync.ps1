# Wrapper to run sync_chapter1_dev_from_prod.py from an Anaconda PowerShell
# Prompt (or regular PowerShell with conda initialized).
#
# Usage:
#   Open "Anaconda Prompt (PowerShell)" from the Start menu
#   cd to the folder containing this script and sync_chapter1_dev_from_prod.py
#   .\run_sync.ps1
#
# If you get an execution-policy error, run this once first:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyScript = Join-Path $ScriptDir "sync_chapter1_dev_from_prod.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "sync_chapter1_dev_from_prod.py not found in $ScriptDir. Make sure both files are in the same folder."
    exit 1
}

# Optionally activate a named conda env first: $env:CONDA_ENV_NAME = "myenv"
if ($env:CONDA_ENV_NAME) {
    conda activate $env:CONDA_ENV_NAME
}

Write-Host "Using Python:" (Get-Command python).Source

# Ensure dependency is present
python -c "import psycopg2" 2>$null
if ($LASTEXITCODE -ne 0) {
    pip install psycopg2-binary
}

# Prompt for connection strings if not already set in this session
if (-not $env:PROD_DATABASE_URL) {
    $secureProd = Read-Host "Enter PROD (ascenda) DATABASE_URL" -AsSecureString
    $env:PROD_DATABASE_URL = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureProd)
    )
}

if (-not $env:DEV_DATABASE_URL) {
    $secureDev = Read-Host "Enter DEV (ascenda-dev) DATABASE_URL" -AsSecureString
    $env:DEV_DATABASE_URL = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureDev)
    )
}

Write-Host ""
Write-Host "Running sync script..."
python $PyScript

# Clear the vars from this session once done
Remove-Item Env:\PROD_DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:\DEV_DATABASE_URL -ErrorAction SilentlyContinue
