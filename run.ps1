Write-Host "Initializing Database..."
cd backend
.\venv\Scripts\activate
python manage.py init_db

Write-Host "Starting Flask Server..."
python run.py
