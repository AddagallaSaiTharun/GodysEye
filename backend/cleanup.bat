@echo off
REM Delete folders and their contents

rd /s /q C:\Users\tharu\OneDrive\Desktop\godseye\backend\logs
rd /s /q C:\Users\tharu\OneDrive\Desktop\godseye\backend\databases

del /f /q C:\Users\tharu\OneDrive\Desktop\godseye\backend\uploaded_videos

echo =========================================
echo Done cleaning the specified folders/files.
echo =========================================
pause