@echo off
echo ================================
echo   GitHub Force Upload
echo ================================
echo.

REM Configure Git user
git config user.name "Nafiz Wasi Khan"
git config user.email "nafizwasikhan@example.com"

REM Initialize if needed
if not exist ".git" (
    git init
)

REM Remove and re-add remote
git remote remove origin 2>nul
git remote add origin https://github.com/NafizWasiKhan/rajbari-ride-backend.git

echo Adding all files...
git add .

echo Committing...
git commit -m "Complete Django backend with Railway config"

echo Creating main branch...
git branch -M main

echo.
echo ================================
echo   FORCE PUSHING to GitHub
echo ================================
echo This will replace everything on GitHub
echo.

git push -u origin main --force

echo.
if errorlevel 1 (
    echo ================================
    echo   Failed!
    echo ================================
    echo Check your internet connection
    echo or GitHub credentials
) else (
    echo ================================
    echo   SUCCESS!
    echo ================================
    echo.
    echo Your code is now on GitHub!
    echo.
    echo Next Steps:
    echo 1. Go to Railway.app
    echo 2. Wait 2-3 minutes for auto-deploy
    echo 3. Check Deploy Logs
    echo.
)

pause
