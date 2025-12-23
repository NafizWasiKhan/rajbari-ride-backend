@echo off
echo ================================
echo   Frontend GitHub Upload
echo ================================
echo.

REM First, let's get the Railway URL
echo Step 1: Update config.js with your Railway URL
echo.
echo Please enter your Railway backend URL (without https://):
echo Example: rajbari-ride.up.railway.app
set /p RAILWAY_URL="Railway URL: "

REM Update config.js
echo.
echo Updating config.js...
cd frontend\js
(
echo // API Configuration
echo // Production Railway URL
echo const API_BASE_URL = "https://%RAILWAY_URL%";
echo.
echo // For local development, use:
echo // const API_BASE_URL = "http://127.0.0.1:8000";
) > config.js
cd ..\..
echo Config updated!
echo.

REM Navigate to frontend folder
cd frontend

REM Initialize git
if not exist ".git" (
    echo Initializing Git repository...
    git init
)

REM Configure git
git config user.name "Nafiz Wasi Khan"
git config user.email "nafizwasikhan@example.com"

REM Remove existing remote
git remote remove origin 2>nul

REM Add remote
echo.
echo Please enter your Frontend GitHub repository URL:
echo Example: https://github.com/YourUsername/rajbari-ride-frontend.git
set /p FRONTEND_REPO="GitHub URL: "
git remote add origin %FRONTEND_REPO%

REM Add all files
echo.
echo Adding files...
git add .

REM Commit
echo Committing...
git commit -m "Frontend ready for Netlify deployment"

REM Push
echo.
echo Pushing to GitHub...
git branch -M main
git push -u origin main --force

echo.
if errorlevel 1 (
    echo ================================
    echo   Push Failed!
    echo ================================
) else (
    echo ================================
    echo   SUCCESS!
    echo ================================
    echo.
    echo Frontend is now on GitHub!
    echo.
    echo Next Steps:
    echo 1. Go to Netlify.com
    echo 2. Click "Add new site"
    echo 3. Connect your GitHub repository
    echo 4. Deploy!
    echo.
)

cd ..
pause
