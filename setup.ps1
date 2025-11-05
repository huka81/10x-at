# Setup script for Windows PowerShell
Write-Host "🏦 Banking Application Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check Python version
Write-Host "`n1. Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.1[1-9]") {
    Write-Host "   ✓ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ✗ Python 3.11+ required. Found: $pythonVersion" -ForegroundColor Red
    exit 1
}

# Check PostgreSQL
Write-Host "`n2. Checking PostgreSQL..." -ForegroundColor Yellow
$psqlVersion = psql --version 2>&1
if ($psqlVersion -match "psql") {
    Write-Host "   ✓ $psqlVersion" -ForegroundColor Green
} else {
    Write-Host "   ✗ PostgreSQL not found. Please install PostgreSQL 14+" -ForegroundColor Red
    exit 1
}

# Install Python dependencies
Write-Host "`n3. Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   ✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
Write-Host "`n4. Setting up environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "   ✓ Created .env file from .env.example" -ForegroundColor Green
    Write-Host "   ⚠ Please update .env with your PostgreSQL credentials" -ForegroundColor Yellow
} else {
    Write-Host "   ✓ .env file already exists" -ForegroundColor Green
}

# Instructions for database setup
Write-Host "`n5. Next steps:" -ForegroundColor Yellow
Write-Host "   a. Update database credentials in .env file" -ForegroundColor White
Write-Host "   b. Create database: createdb banking_app" -ForegroundColor White
Write-Host "   c. Run migrations: yoyo apply --config yoyo.ini" -ForegroundColor White
Write-Host "   d. Run tests: pytest" -ForegroundColor White
Write-Host "   e. Start app: streamlit run app.py" -ForegroundColor White

Write-Host "`n✓ Setup complete!" -ForegroundColor Green
Write-Host "Read MIGRATION.md for details about the TypeScript to Python migration.`n" -ForegroundColor Cyan
