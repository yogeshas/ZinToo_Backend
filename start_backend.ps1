Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "Starting Flask backend..." -ForegroundColor Cyan
python app.py

Read-Host "Press Enter to continue..."
