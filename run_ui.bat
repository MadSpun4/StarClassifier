@echo off
rem Keep this file in UTF-8 with BOM and CRLF so cmd.exe parses it correctly.
setlocal EnableExtensions
chcp 65001 >nul

set "ROOT=%~dp0"
cd /d "%ROOT%"

call :resolve_python
if errorlevel 1 goto :fail_python

if not exist ".venv\Scripts\python.exe" (
    echo Создаю виртуальное окружение...
    call %PYTHON_CMD% -m venv ".venv"
    if errorlevel 1 goto :fail_setup
)

set "VENV_PYTHON=.venv\Scripts\python.exe"
set "STAMP_FILE=.venv\requirements.installed.txt"
set "NEED_INSTALL="

if not exist "%STAMP_FILE%" set "NEED_INSTALL=1"
if exist "%STAMP_FILE%" (
    fc /b "requirements.txt" "%STAMP_FILE%" >nul
    if errorlevel 1 set "NEED_INSTALL=1"
)

if defined NEED_INSTALL (
    echo Устанавливаю зависимости...
    call "%VENV_PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 goto :fail_setup

    call "%VENV_PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 goto :fail_setup

    copy /y "requirements.txt" "%STAMP_FILE%" >nul
)

if /I "%STAR_CLASSIFIER_SKIP_RUN%"=="1" (
    echo Подготовка завершена. Запуск пропущен, потому что STAR_CLASSIFIER_SKIP_RUN=1.
    exit /b 0
)

echo Запускаю приложение...
call "%VENV_PYTHON%" main.py
exit /b %errorlevel%

:resolve_python
where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    exit /b 0
)

exit /b 1

:fail_python
echo Python 3.10 или новее не найден в PATH.
echo Установите Python и запустите этот файл снова.
pause
exit /b 1

:fail_setup
echo Не удалось подготовить окружение или установить зависимости.
pause
exit /b 1
