@echo off
REM Test runner script for Token Metrics Monitor (Windows)

echo.
echo ====================================================================
echo Running Token Metrics Monitor Test Suite...
echo ====================================================================
echo.

REM Install test dependencies
echo [1/2] Installing test dependencies...
pip install -q -r tests\requirements-test.txt
if errorlevel 1 (
    echo ERROR: Failed to install test dependencies
    pause
    exit /b 1
)

REM Run tests with coverage
echo.
echo [2/2] Running tests with coverage...
pytest tests\ -v --cov=src --cov-report=term-missing --cov-report=html
if errorlevel 1 (
    echo.
    echo WARNING: Some tests failed
) else (
    echo.
    echo ====================================================================
    echo Test suite complete!
    echo ====================================================================
    echo.
    echo Coverage report saved to htmlcov\index.html
)

echo.
pause
