@echo off
REM Quick test runner for RSS Summarizer

echo ========================================
echo RSS Summarizer - Test Runner
echo ========================================
echo.

if "%1"=="full" (
    echo Running FULL test suite (includes refresh/clear)...
    echo This will take approximately 60 seconds.
    echo.
    python test_app_features.py --full
) else if "%1"=="quick" (
    echo Running QUICK test suite (excludes refresh/clear)...
    echo This will take approximately 5 seconds.
    echo.
    python test_app_features.py
) else (
    echo Usage:
    echo   run_tests.bat quick  - Run quick tests (5 seconds)
    echo   run_tests.bat full   - Run full tests (60 seconds)
    echo.
    echo Running QUICK tests by default...
    echo.
    python test_app_features.py
)

echo.
echo ========================================
echo Test execution complete
echo ========================================
pause
