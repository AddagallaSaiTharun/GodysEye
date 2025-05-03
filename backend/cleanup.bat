@echo off
REM Delete folders and their contents

rd /s /q C:\Users\tharu\OneDrive\Desktop\godseye\backend\video_db
rd /s /q C:\Users\tharu\OneDrive\Desktop\godseye\backend\video_db_missing
rd /s /q C:\Users\tharu\OneDrive\Desktop\godseye\backend\missing_person
rd /s /q C:\Users\tharu\OneDrive\Desktop\godseye\backend\logs

REM Delete the specific JSON file
del /f /q C:\Users\tharu\OneDrive\Desktop\godseye\backend\database\MissingPersons.json
del /f /q C:\Users\tharu\OneDrive\Desktop\godseye\backend\uploaded_videos

echo =========================================
echo Done cleaning the specified folders/files.
echo =========================================
pause