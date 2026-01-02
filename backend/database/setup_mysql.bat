@echo off
echo =========================================
echo Sinhala Plagiarism Detection - MySQL Setup
echo =========================================
echo.

REM Check if MySQL is installed
where mysql >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: MySQL is not installed or not in PATH
    echo.
    echo Please install MySQL:
    echo   1. Download from https://dev.mysql.com/downloads/mysql/
    echo   2. Or use XAMPP: https://www.apachefriends.org/
    echo   3. Or use WAMP: https://www.wampserver.com/
    echo.
    pause
    exit /b 1
)

echo MySQL found. Checking if server is running...
echo.

REM Try to connect to MySQL
mysql -u root -proot -e "SELECT 1" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo MySQL server is not running or credentials are wrong.
    echo.
    echo Please:
    echo   1. Start MySQL server (via XAMPP Control Panel, Services, or command line)
    echo   2. Make sure user 'root' with password 'root' exists
    echo   3. Or update credentials in db_config.py
    echo.
    pause
    exit /b 1
)

echo MySQL server is running!
echo.
echo Creating database and tables...
echo.

mysql -u root -proot < "%~dp0setup_database.sql"
if %ERRORLEVEL% EQU 0 (
    echo.
    echo =========================================
    echo SUCCESS! Database setup complete.
    echo Database: sinhala_plagiarism_db
    echo =========================================
) else (
    echo.
    echo ERROR: Failed to create database/tables.
    echo Check the error message above.
)

echo.
pause
