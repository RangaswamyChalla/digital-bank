@echo off
REM ===== BANKING PLATFORM - INTEGRATED DEPLOYMENT SCRIPT (WINDOWS) =====
REM Quick start for running the complete integrated system on Windows
REM Usage: deploy.bat [start|stop|logs|clean]

setlocal enabledelayedexpansion

REM ===== FUNCTIONS =====

:check_requirements
echo.
echo ========================================
echo Checking Requirements
echo ========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Docker not found. Please install Docker Desktop for Windows.
    exit /b 1
)
echo [OK] Docker is installed

REM Check Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Docker Compose not found.
    exit /b 1
)
echo [OK] Docker Compose is installed

REM Check .env file
if not exist ".env" (
    echo [INFO] .env file not found. Creating from .env.example
    copy .env.example .env
    echo [OK] .env created (update with your values)
)

goto:eof

:start_system
echo.
echo ========================================
echo Starting Banking Platform
echo ========================================
echo.

echo [INFO] Building containers...
call docker-compose build
if %errorlevel% neq 0 (
    echo [X] Failed to build containers
    exit /b 1
)
echo [OK] Containers built
echo.

echo [INFO] Starting services...
call docker-compose up -d
if %errorlevel% neq 0 (
    echo [X] Failed to start services
    exit /b 1
)
echo [OK] Services started
echo.

echo [INFO] Waiting for services to be ready...
timeout /t 10 /nobreak

echo.
echo ========================================
echo Service Health Status
echo ========================================
echo.

REM Check backend
for /f %%i in ('curl -s -o /dev/null -w "%%{http_code}" http://localhost:8000/health') do set backend_status=%%i
if "%backend_status%"=="200" (
    echo [OK] Backend is healthy ^(http://localhost:8000^)
) else (
    echo [X] Backend is not responding
)

REM Check frontend (just check port)
netstat -ano | findstr ":5173 " >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Frontend is running ^(http://localhost:5173^)
) else (
    echo [X] Frontend is not responding
)

echo.
echo ========================================
echo System Started Successfully
echo ========================================
echo.
echo Access Points:
echo   - Frontend:      http://localhost:5173
echo   - Backend API:   http://localhost:8000
echo   - API Docs:      http://localhost:8000/docs
echo   - Database:      localhost:5432
echo.
echo Default Credentials:
echo   - Admin Email:   admin@digitalbank.com
echo   - Admin Pass:    Admin@123456
echo.

goto:eof

:stop_system
echo.
echo ========================================
echo Stopping Banking Platform
echo ========================================
echo.

call docker-compose down
if %errorlevel% equ 0 (
    echo [OK] Services stopped
) else (
    echo [X] Failed to stop services
)

goto:eof

:show_logs
echo.
echo ========================================
echo Service Logs
echo ========================================
echo.

if "%1"=="backend" (
    call docker-compose logs -f backend
) else if "%1"=="frontend" (
    call docker-compose logs -f frontend
) else if "%1"=="db" (
    call docker-compose logs -f db
) else (
    call docker-compose logs -f
)

goto:eof

:clean_system
echo.
echo ========================================
echo Cleaning System
echo ========================================
echo.

call docker-compose down -v
if %errorlevel% equ 0 (
    echo [OK] Containers and volumes removed
) else (
    echo [X] Failed to clean system
)

echo.
echo [INFO] Note: Source code and configuration files preserved
echo.

goto:eof

:show_status
echo.
echo ========================================
echo System Status
echo ========================================
echo.

call docker-compose ps

goto:eof

:test_integration
echo.
echo ========================================
echo Running Integration Tests
echo ========================================
echo.

call docker-compose exec backend python integration_tests.py

goto:eof

REM ===== MAIN MENU =====

echo.
echo ========================================
echo Banking Platform - Integrated System
echo ========================================
echo.

if "%1"=="" goto start
if /i "%1"=="start" goto start
if /i "%1"=="stop" goto stop
if /i "%1"=="restart" goto restart
if /i "%1"=="logs" goto logs
if /i "%1"=="status" goto status
if /i "%1"=="clean" goto clean
if /i "%1"=="test" goto test

echo Usage: deploy.bat [start^|stop^|restart^|logs^|status^|clean^|test]
echo.
echo Commands:
echo   start       - Start all services
echo   stop        - Stop all services
echo   restart     - Restart all services
echo   logs        - Show service logs (optionally specify: backend^|frontend^|db)
echo   status      - Show services status
echo   clean       - Stop and remove containers/volumes
echo   test        - Run integration tests
exit /b 1

:start
call :check_requirements
call :start_system
goto final

:stop
call :stop_system
goto final

:restart
call :stop_system
timeout /t 2 /nobreak
call :start_system
goto final

:logs
call :show_logs %2
goto final

:status
call :show_status
goto final

:clean
call :clean_system
goto final

:test
call :test_integration
goto final

:final
endlocal
