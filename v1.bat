REM Title of the application
title Automated File Copier Setup

REM === Configuration Variables ===
set SOURCE_DIR=%~dp0
set TARGET_DIR=C:\AutomatedFileCopier
set LOG_FILE=%SOURCE_DIR%\setup.log
set PYTHON_PATH=

REM Create or clear the log file
echo Starting setup... > %LOG_FILE%
echo ===================================== >> %LOG_FILE%
echo Automated File Copier Setup Log >> %LOG_FILE%
echo ===================================== >> %LOG_FILE%

REM === Step 1: Check if Python is Installed ===
echo Checking for Python installation... >> %LOG_FILE%
python --version >nul 2>&1
if %errorlevel% EQU 0 (
    echo [SUCCESS] Python is already installed. Proceeding with setup... >> %LOG_FILE%
    for /f "delims=" %%P in ('where python') do set PYTHON_PATH=%%P
    echo [INFO] Python executable located at: %PYTHON_PATH% >> %LOG_FILE%
) else (
    echo [ERROR] Python is not installed. Please install Python manually and rerun this setup. >> %LOG_FILE%
    pause
    exit /b
)

REM === Step 2: Verify Python Installation ===
echo Verifying Python installation... >> %LOG_FILE%
"%PYTHON_PATH%" --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [ERROR] Unable to verify Python installation at %PYTHON_PATH%. Exiting setup. >> %LOG_FILE%
    pause
    exit /b
) else (
    echo [SUCCESS] Python installation verified. Proceeding with setup... >> %LOG_FILE%
)

REM === Step 3: Ensure pip Is Installed ===
echo Checking for pip installation... >> %LOG_FILE%
"%PYTHON_PATH%" -m pip --version >nul 2>&1
if %errorlevel% NEQ 0 (
    echo [ERROR] pip is not installed. Please install pip manually and rerun this setup. >> %LOG_FILE%
    pause
    exit /b
) else (
    echo [INFO] pip is already installed. Proceeding... >> %LOG_FILE%
)

REM === Step 4: Copy Files to Target Directory ===
echo Copying files to target directory: %TARGET_DIR% >> %LOG_FILE%
if not exist %TARGET_DIR% (
    mkdir %TARGET_DIR%
    echo Created folder %TARGET_DIR%. >> %LOG_FILE%
) else (
    echo Folder %TARGET_DIR% already exists. Proceeding with file copy... >> %LOG_FILE%
)

xcopy %SOURCE_DIR%\* %TARGET_DIR% /E /I /Y >> %LOG_FILE%
if %errorlevel% NEQ 0 (
    echo [ERROR] File copy operation failed. Exiting setup. >> %LOG_FILE%
    pause
    exit /b
) else (
    echo [SUCCESS] Files copied to %TARGET_DIR%. Proceeding... >> %LOG_FILE%
)

REM === Step 5: Create Background Scheduler Script ===
echo Creating VBS file for background scheduler... >> %LOG_FILE%
set VBS_FILE_BG=%TARGET_DIR%\run_bg.vbs
echo Set objShell = CreateObject("WScript.Shell") > %VBS_FILE_BG%
echo objShell.Run "%PYTHON_PATH% %TARGET_DIR%\background_schedular.py", 0, False >> %VBS_FILE_BG%
if exist %VBS_FILE_BG% (
    echo [SUCCESS] Background scheduler created in %TARGET_DIR%. >> %LOG_FILE%
) else (
    echo [ERROR] Failed to create background scheduler. Exiting setup. >> %LOG_FILE%
    pause
    exit /b
)

REM Add Background Scheduler to Startup Folder
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
copy /Y %VBS_FILE_BG% "%STARTUP_FOLDER%" >> %LOG_FILE%
if %errorlevel% NEQ 0 (
    echo [ERROR] Failed to copy background scheduler. Exiting setup. >> %LOG_FILE%
    pause
    exit /b
) else (
    echo [SUCCESS] Background scheduler added to Startup. >> %LOG_FILE%
)

REM === Step 6: Create Desktop Shortcut for main.py ===
echo Creating desktop shortcut for main.py... >> %LOG_FILE%
set VBS_FILE_DESKTOP=%TARGET_DIR%\run_main.vbs
echo Set objShell = CreateObject("WScript.Shell") > %VBS_FILE_DESKTOP%
echo objShell.Run "%PYTHON_PATH% %TARGET_DIR%\main.py", 0, False >> %VBS_FILE_DESKTOP%

if exist %VBS_FILE_DESKTOP% (
    echo [SUCCESS] VBS file for main.py created: %VBS_FILE_DESKTOP%. >> %LOG_FILE%
) else (
    echo [ERROR] Failed to create VBS file for main.py script. Exiting setup. >> %LOG_FILE%
    pause
    exit /b
)

REM Create Desktop Shortcut
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_NAME=Automated File Copier.lnk

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $shortcut = $ws.CreateShortcut('%DESKTOP%\%SHORTCUT_NAME%'); $shortcut.TargetPath = '%VBS_FILE_DESKTOP%'; $shortcut.WorkingDirectory = '%TARGET_DIR%'; $shortcut.IconLocation = '%SYSTEMROOT%\System32\shell32.dll,44'; $shortcut.Save();" >> %LOG_FILE%
if exist "%DESKTOP%\%SHORTCUT_NAME%" (
    echo [SUCCESS] Desktop shortcut created successfully for main.py. >> %LOG_FILE%
) else (
    echo [ERROR] Failed to create desktop shortcut for main.py script. Exiting setup. >> %LOG_FILE%
    pause
    exit /b
)

REM === Final Completion Message ===
echo =============================================== >> %LOG_FILE%
echo Setup is complete! >> %LOG_FILE%
echo - Background scheduler added to startup folder. >> %LOG_FILE%
echo - Desktop shortcut created for main.py. >> %LOG_FILE%
echo ===============================================

REM === Offer to Restart the System ===
echo Restarting the computer is recommended to ensure setup changes are applied.
choice /c YN /m "Do you want to restart the computer now?"
if %errorlevel% EQU 1 (
    echo Restarting the computer... >> %LOG_FILE%
    shutdown /r /t 0
) else (
    echo Restart canceled. You can restart manually later. >> %LOG_FILE%
)

pause
exit /b 0
