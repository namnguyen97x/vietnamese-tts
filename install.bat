@echo off
echo ========================================
echo    Vietnamese TTS Application Setup
echo ========================================
echo.

echo Dang kiem tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Loi: Python khong duoc cai dat hoac khong co trong PATH
    echo Vui long cai dat Python 3.7+ tu https://python.org
    pause
    exit /b 1
)

echo Python da duoc cai dat.
echo.

echo Dang cai dat cac thu vien can thiet...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Co loi xay ra khi cai dat. Vui long kiem tra:
    echo 1. Ket noi internet
    echo 2. Quyen admin (neu can)
    echo 3. Python version (can 3.7+)
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Cai dat thanh cong!
echo ========================================
echo.
echo De chay ung dung, su dung lenh:
echo python main.py
echo.
echo Hoac chay file run.bat
echo.
pause 