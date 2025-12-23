@echo off
echo ================================
echo   GitHub Upload Script
echo ================================
echo.

REM Check if this is a git repository
if not exist ".git" (
    echo Initializing Git repository...
    git init
    echo.
)

REM Check if remote exists
git remote -v | findstr origin >nul 2>&1
if errorlevel 1 (
    echo Please enter your GitHub repository URL:
    echo Example: https://github.com/YourUsername/rajbari-ride-backend.git
    set /p REPO_URL="GitHub URL: "
    git remote add origin %REPO_URL%
    echo.
)

echo Adding all files...
git add .
echo.

echo Committing changes...
git commit -m "Complete backend with Railway config"
echo.

echo Pushing to GitHub...
echo (You may need to enter GitHub credentials)
git branch -M main
git push -u origin main --force
echo.

echo ================================
echo   Upload Complete!
echo ================================
echo.
echo Next: Go to Railway and wait for auto-deploy
pause
