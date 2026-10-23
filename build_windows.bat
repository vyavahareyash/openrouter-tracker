@echo off
echo ========================================================
echo       Building OpenRouter Tracker for Windows
echo ========================================================

python build_windows.py %*
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] Windows Build Complete!
