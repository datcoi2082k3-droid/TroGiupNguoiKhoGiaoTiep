@echo off
echo Đang cài đặt thư viện cần thiết...
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
echo Đang khởi động ứng dụng...
.\.venv\Scripts\python.exe main.py
pause
