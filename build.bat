@echo off
chcp 65001 >nul
echo =========================================
echo    Сборка AssistPiip
echo =========================================

call .venv\Scripts\activate

echo Установка PyInstaller...
pip install pyinstaller >nul

echo Очистка старых файлов...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "AssistPiip-Beta-1.0.0.zip" del "AssistPiip-Beta-1.0.0.zip"

echo Запуск PyInstaller...
pyinstaller --noconfirm --windowed --name "AssistPiip" --icon "icon.ico" --add-data "icons;icons" --add-data "app_icon.png;." --add-data "icon.ico;." main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ОШИБКА] PyInstaller завершился с ошибкой.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Небольшая пауза, чтобы файлы освободились...
timeout /t 3 >nul

echo Упаковка в ZIP архив через Python...
python -c "import shutil; shutil.make_archive('AssistPiip-Beta-1.0.0', 'zip', 'dist/AssistPiip')"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ОШИБКА] Не удалось создать ZIP архив.
    echo Попробуйте закрыть все процессы AssistPiip.exe и повторить.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =========================================
echo Готово! Архив создан: AssistPiip-Beta-1.0.0.zip
echo Папка для теста: dist\AssistPiip\AssistPiip.exe
echo =========================================
pause
