@echo off
echo ============================================
echo  Google Custom Search API Setup
echo ============================================
echo.

REM Check if credentials are provided as arguments
if "%~1"=="" (
    echo Please enter your Google API Key:
    set /p GOOGLE_API_KEY=API Key:
) else (
    set GOOGLE_API_KEY=%~1
)

if "%~2"=="" (
    echo.
    echo Please enter your Search Engine ID (CSE_ID):
    set /p CSE_ID=CSE ID:
) else (
    set CSE_ID=%~2
)

echo.
echo Setting environment variables...

REM Set for current session
set GOOGLE_API_KEY=%GOOGLE_API_KEY%
set CSE_ID=%CSE_ID%

REM Set permanently for user
setx GOOGLE_API_KEY "%GOOGLE_API_KEY%" >nul 2>&1
setx CSE_ID "%CSE_ID%" >nul 2>&1

echo.
echo ============================================
echo  Configuration Complete!
echo ============================================
echo.
echo GOOGLE_API_KEY: %GOOGLE_API_KEY:~0,10%...
echo CSE_ID: %CSE_ID%
echo.
echo Environment variables set for:
echo  - Current session
echo  - Permanently (user level)
echo.
echo You can now start the backend server:
echo   python -m uvicorn main:app --reload --port 8000
echo.
echo Test the API at:
echo   http://localhost:8000/api/algorithms
echo.
pause
