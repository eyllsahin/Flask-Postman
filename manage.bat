@echo off
echo ================================================
echo           Flask Chatbot Manager
echo ================================================
echo.

:menu
echo Choose an option:
echo 1. Start Docker containers
echo 2. Stop Docker containers
echo 3. Show container status
echo 4. Start local Flask app (port 5001)
echo 5. Check system status
echo 6. View logs
echo 7. Exit
echo.

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto start_docker
if "%choice%"=="2" goto stop_docker
if "%choice%"=="3" goto status
if "%choice%"=="4" goto start_local
if "%choice%"=="5" goto check_status
if "%choice%"=="6" goto logs
if "%choice%"=="7" goto exit
goto invalid

:start_docker
echo.
echo Starting Docker containers...
docker-compose up -d
echo.
echo Containers started! Check status below:
docker-compose ps
echo.
echo Application URLs:
echo   Docker: http://localhost:8080
echo   Health: http://localhost:8080/health
echo.
pause
goto menu

:stop_docker
echo.
echo Stopping Docker containers...
docker-compose down
echo Containers stopped!
echo.
pause
goto menu

:status
echo.
echo Container Status:
docker-compose ps
echo.
pause
goto menu

:start_local
echo.
echo Starting local Flask application...
echo Will be available at: http://localhost:5001
echo Make sure your .env has: DB_HOST=localhost and DB_PORT=3307
echo Press Ctrl+C to stop the application
echo.
python run.py
pause
goto menu

:check_status
echo.
echo Checking Docker...
docker --version
docker ps
echo.
echo Checking ports...
netstat -an | findstr ":8080"
netstat -an | findstr ":3307"
netstat -an | findstr ":5001"
echo.
pause
goto menu

:logs
echo.
echo Recent logs:
docker-compose logs --tail=30
echo.
pause
goto menu

:invalid
echo Invalid choice. Please enter 1-7.
echo.
goto menu

:exit
echo.
echo Goodbye!
pause
