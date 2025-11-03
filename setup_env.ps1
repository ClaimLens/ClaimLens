# ClaimLens Environment Setup Script for Windows PowerShell
# This script creates and configures the conda environment for ClaimLens

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ClaimLens Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if conda is available
$condaAvailable = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaAvailable) {
    Write-Host "ERROR: conda is not found in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Miniconda first:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Yellow
    Write-Host "2. Run the installer" -ForegroundColor Yellow
    Write-Host "3. After installation, run: conda init powershell" -ForegroundColor Yellow
    Write-Host "4. Restart PowerShell and run this script again" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "Step 1: Creating conda environment 'claimlens' with Python 3.11..." -ForegroundColor Green
conda create -n claimlens python=3.11 -y

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create conda environment" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Activating environment..." -ForegroundColor Green
conda activate claimlens

Write-Host ""
Write-Host "Step 3: Upgrading pip, setuptools, and wheel..." -ForegroundColor Green
python -m pip install --upgrade pip setuptools wheel

Write-Host ""
Write-Host "Step 4: Installing binary dependencies from conda-forge (to avoid build issues)..." -ForegroundColor Green
conda install -c conda-forge grpcio protobuf pillow pydantic-core -y

Write-Host ""
Write-Host "Step 5: Installing project dependencies from requirements.txt..." -ForegroundColor Green
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 6: Verifying installation..." -ForegroundColor Green
python -c "import flask, pydantic, pymongo, google.generativeai; print('All core imports successful')"

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Some imports failed. Check error messages above." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Setup Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To activate this environment in the future, run:" -ForegroundColor Yellow
    Write-Host "  conda activate claimlens" -ForegroundColor White
    Write-Host ""
    Write-Host "To run the application:" -ForegroundColor Yellow
    Write-Host "  python app.py" -ForegroundColor White
    Write-Host ""
    Write-Host "To run tests:" -ForegroundColor Yellow
    Write-Host "  python -m pytest" -ForegroundColor White
    Write-Host ""
}
