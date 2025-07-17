@echo off
echo ========================================
echo Building Gomobot with Modular Compilation
echo ========================================

REM Clean previous build
if exist "dist" rmdir /s /q "dist"
if exist "*.build" rmdir /s /q "*.build"
if exist "*.dist" rmdir /s /q "*.dist"

echo Cleaning previous build files...

REM Install all dependencies from requirements.txt
echo Installing dependencies from requirements.txt...
py -m pip install -r requirements.txt
py -m pip install requests

REM Create dist directory
mkdir dist

echo ========================================
echo Step 1: Compiling UI module to PYD
echo ========================================

py -m nuitka ^
    --module ^
    --assume-yes-for-downloads ^
    --enable-plugin=tk-inter ^
    --include-module=tkinter ^
    --include-module=tkinter.ttk ^
    --include-module=tkinter.filedialog ^
    --include-module=tkinter.messagebox ^
    --include-module=ttkbootstrap ^
    --output-dir=dist ^
    ui

if %errorlevel% neq 0 (
    echo UI module compilation failed!
    pause
    exit /b 1
)

echo ========================================
echo Step 2: Compiling PYGOMO module to PYD
echo ========================================

py -m nuitka ^
    --module ^
    --assume-yes-for-downloads ^
    --include-module=threading ^
    --include-module=queue ^
    --include-module=subprocess ^
    --output-dir=dist ^
    pygomo

if %errorlevel% neq 0 (
    echo PYGOMO module compilation failed!
    pause
    exit /b 1
)

echo ========================================
echo Step 3: Compiling UTILS module to PYD
echo ========================================

py -m nuitka ^
    --module ^
    --assume-yes-for-downloads ^
    --include-module=numpy ^
    --include-module=cv2 ^
    --include-module=PIL ^
    --include-module=PIL.Image ^
    --include-module=PIL.ImageTk ^
    --include-module=mss ^
    --include-module=keyboard ^
    --include-module=psutil ^
    --include-module=win32api ^
    --include-module=win32con ^
    --include-module=win32gui ^
    --include-module=win32process ^
    --include-module=scipy ^
    --output-dir=dist ^
    utils

if %errorlevel% neq 0 (
    echo UTILS module compilation failed!
    pause
    exit /b 1
)

echo ========================================
echo Step 4: Compiling main.py to EXE
echo ========================================

py -m nuitka ^
    --standalone ^
    --assume-yes-for-downloads ^
    --enable-plugin=tk-inter ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=icon.ico ^
    --include-data-files=color.cfg=color.cfg ^
    --include-data-files=tool_config.toml=tool_config.toml ^
    --include-data-files=ReadMe.md=ReadMe.md ^
    --include-data-files=requirements.txt=requirements.txt ^
    --include-module=tkinter ^
    --include-module=tkinter.ttk ^
    --include-module=tkinter.filedialog ^
    --include-module=tkinter.messagebox ^
    --include-module=keyboard ^
    --include-module=mss ^
    --include-module=numpy ^
    --include-module=cv2 ^
    --include-module=PIL ^
    --include-module=PIL.Image ^
    --include-module=PIL.ImageTk ^
    --include-module=psutil ^
    --include-module=win32api ^
    --include-module=win32con ^
    --include-module=win32gui ^
    --include-module=win32process ^
    --include-module=tomllib ^
    --include-module=scipy ^
    --include-module=ttkbootstrap ^
    --include-module=threading ^
    --include-module=queue ^
    --include-module=json ^
    --include-module=subprocess ^
    --include-module=configparser ^
    --include-module=requests ^
    --include-module=urllib ^
    --include-module=urllib.request ^
    --include-module=zipfile ^
    --include-module=shutil ^
    --output-dir=dist ^
    --output-filename=AutoGomoku.exe ^
    main.py

if %errorlevel% neq 0 (
    echo Main executable compilation failed!
    pause
    exit /b 1
)

echo ========================================
echo Step 5: Organizing build output
echo ========================================

REM Copy PYD files to the main executable directory
if exist "dist\ui.pyd" copy "dist\ui.pyd" "dist\main.dist\"
if exist "dist\pygomo.pyd" copy "dist\pygomo.pyd" "dist\main.dist\"
if exist "dist\utils.pyd" copy "dist\utils.pyd" "dist\main.dist\"

REM Copy additional files
if exist "color.cfg" copy "color.cfg" "dist\main.dist\"
if exist "tool_config.toml" copy "tool_config.toml" "dist\main.dist\"

REM Create version info file for updates
echo Creating version info...
echo v1.0.0 > "dist\main.dist\version.txt"

echo ========================================
echo Step 6: Cleanup
echo ========================================

REM Clean up individual build artifacts
if exist "ui.build" rmdir /s /q "ui.build"
if exist "pygomo.build" rmdir /s /q "pygomo.build"
if exist "utils.build" rmdir /s /q "utils.build"
if exist "main.build" rmdir /s /q "main.build"

REM Clean up individual PYD files from dist root
if exist "dist\ui.pyd" del "dist\ui.pyd"
if exist "dist\pygomo.pyd" del "dist\pygomo.pyd"
if exist "dist\utils.pyd" del "dist\utils.pyd"

echo ========================================
echo Build completed successfully!
echo ========================================
echo Main executable: dist\main.dist\Gomobot.exe
echo Modular components:
echo   - dist\main.dist\ui.pyd
echo   - dist\main.dist\pygomo.pyd
echo   - dist\main.dist\utils.pyd
echo ========================================
echo For updates, you can now replace individual .pyd files
echo without rebuilding the entire application!
echo ========================================

pause