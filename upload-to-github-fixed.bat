@echo off
echo ================================
echo   GitHub Upload Script (Fixed)
echo ================================
echo.

REM Configure Git user (if not already configured)
echo Setting up Git user...
git config user.name "Nafiz Wasi Khan"
git config user.email "nafizwasikhan@example.com"
echo Git user configured!
echo.

REM Check if this is a git repository
if not exist ".git" (
    echo Initializing Git repository...
    git init
    echo.
)

REM Remove existing remote if it exists (to avoid conflict)
git remote remove origin 2>nul

REM Add remote
echo Please enter your GitHub repository URL:
echo Example: https://github.com/YourUsername/rajbari-ride-backend.git
set /p REPO_URL="GitHub URL: "
git remote add origin %REPO_URL%
echo Remote added!
echo.

echo Adding all files...
git add .
echo.

echo Committing changes...
git commit -m "Complete backend with Railway config and PostgreSQL support"
echo.

echo Creating main branch...
git branch -M main
echo.

echo Pushing to GitHub...
echo (You may need to enter GitHub username and Personal Access Token)
echo.
git push -u origin main
echo.

if errorlevel 1 (
    echo.
    echo ================================
    echo   Push Failed!
    echo ================================
    echo.
    echo If authentication failed, you need a Personal Access Token.
    echo.
    echo How to create one:
    echo 1. Go to: https://github.com/settings/tokens
    echo 2. Click "Generate new token (classic)"
    echo 3. Select "repo" scope
    echo 4. Generate and copy the token
    echo 5. Use the token as your password when prompted
    echo.
) else (
    echo.
    echo ================================
    echo   Upload Successful!
    echo ================================
    echo.
    echo Next: Go to Railway dashboard
    echo Your project will auto-deploy in 2-3 minutes
    echo.
)

pause
