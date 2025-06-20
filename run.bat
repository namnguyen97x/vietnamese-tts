@echo off
echo ========================================
echo    Vietnamese TTS Application
echo ========================================
echo.

echo Dang khoi dong ung dung...
python main.py

if errorlevel 1 (
    echo.
    echo Co loi xay ra khi chay ung dung.
    echo Vui long kiem tra:
    echo 1. Da cai dat cac thu vien chua? (chay install.bat)
    echo 2. File main.py co ton tai khong?
    echo 3. Python version (can 3.7+)
    pause
) 