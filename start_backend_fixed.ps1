Write-Host "🚀 Starting Backend with All Fixes Applied" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "📦 Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create missing directories
Write-Host "📁 Creating missing directories..." -ForegroundColor Yellow
$directories = @(
    "assets/img/widgets",
    "assets/img/categories", 
    "assets/img/products",
    "migrations/versions"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "✅ Created directory: $dir" -ForegroundColor Green
    }
}

# Fix any remaining circular imports
Write-Host "🔧 Fixing circular imports..." -ForegroundColor Yellow
Get-ChildItem models\*.py | ForEach-Object { 
    (Get-Content $_.FullName) -replace 'from app import db', 'from extensions import db' | Set-Content $_.FullName 
}
Get-ChildItem services\*.py | ForEach-Object { 
    (Get-Content $_.FullName) -replace 'from app import db', 'from extensions import db' | Set-Content $_.FullName 
}
Get-ChildItem routes\*.py | ForEach-Object { 
    (Get-Content $_.FullName) -replace 'from app import db', 'from extensions import db' | Set-Content $_.FullName 
}

Write-Host "✅ All fixes applied!" -ForegroundColor Green

# Start the backend
Write-Host "🚀 Starting Flask backend..." -ForegroundColor Cyan
Write-Host "Backend will be available at: http://localhost:5000" -ForegroundColor Green
Write-Host "Health check: http://localhost:5000/api/health" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "=" * 50 -ForegroundColor Cyan

python app.py

Read-Host "Press Enter to continue..."
