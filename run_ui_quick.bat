@echo off
rem Keep this file in UTF-8 with BOM and CRLF so cmd.exe parses it correctly.
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist ".venv\Scripts\python.exe" goto :missing_venv

echo Запускаю приложение...
call ".venv\Scripts\python.exe" main.py
exit /b %errorlevel%

:missing_venv
echo Виртуальное окружение .venv не найдено.
echo Сначала один раз запустите run_ui.bat, чтобы подготовить окружение.
pause
exit /b 1
