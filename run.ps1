Write-Host "Initializing Database..."
.\venv\Scripts\activate
python manage.py init_db

Write-Host "Starting Flask Server..."
python backend/run.py
