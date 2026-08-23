@echo off
echo ==================================================
echo    STARTING CALDER COUNTY FULL-STACK APP          
echo ==================================================
echo.

echo Seeding database...
python backend\seed_database.py

echo Starting FastAPI Backend on http://localhost:8000 ...
start "Backend FastAPI" cmd /k "uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting React Frontend on http://localhost:5173 ...
start "Frontend React" cmd /k "cd frontend && npm run dev"

echo.
echo ==================================================
echo    Full-Stack App Launched Successfully!          
echo    Frontend: http://localhost:5173                
echo    Backend:  http://localhost:8000                
echo    Swagger:  http://localhost:8000/docs           
echo ==================================================
