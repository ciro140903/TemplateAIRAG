@echo off
setlocal enabledelayedexpansion

set BACKUP_DATE=%date:~10,4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
set BACKUP_DATE=!BACKUP_DATE: =0!

echo ===============================================
echo      PORTALE AZIENDALE - BACKUP SISTEMA
echo ===============================================
echo Data: %BACKUP_DATE%
echo.

if not exist "backups" mkdir "backups"
set BACKUP_DIR=backups\backup_%BACKUP_DATE%
mkdir "%BACKUP_DIR%"

echo [1/5] Backup MongoDB...
docker compose exec mongodb mongodump --host localhost --port 27017 --username admin --password portal_mongo_2024 --authenticationDatabase admin --out /backup/mongodb_%BACKUP_DATE% 2>nul
if %errorlevel% equ 0 (
    echo [OK] Backup MongoDB completato
    xcopy "data\mongodb\backup\mongodb_%BACKUP_DATE%" "%BACKUP_DIR%\mongodb\" /e /i /q >nul
) else (
    echo [ERRORE] Backup MongoDB fallito
)

echo [2/5] Backup Qdrant...
docker compose exec qdrant tar -czf /qdrant/storage/backup_qdrant_%BACKUP_DATE%.tar.gz -C /qdrant/storage/ . 2>nul
if %errorlevel% equ 0 (
    echo [OK] Backup Qdrant completato
    copy "data\qdrant\backup_qdrant_%BACKUP_DATE%.tar.gz" "%BACKUP_DIR%\" >nul
) else (
    echo [ERRORE] Backup Qdrant fallito
)

echo [3/5] Backup configurazioni...
xcopy "monitoring" "%BACKUP_DIR%\monitoring\" /e /i /q >nul
xcopy "nginx" "%BACKUP_DIR%\nginx\" /e /i /q >nul
copy ".env" "%BACKUP_DIR%\" >nul
copy "docker-compose.yml" "%BACKUP_DIR%\" >nul
echo [OK] Backup configurazioni completato

echo [4/5] Backup logs...
xcopy "logs" "%BACKUP_DIR%\logs\" /e /i /q >nul
echo [OK] Backup logs completato

echo [5/5] Compressione backup...
powershell -command "Compress-Archive -Path '%BACKUP_DIR%\*' -DestinationPath 'backups\portal_backup_%BACKUP_DATE%.zip' -Force"
if %errorlevel% equ 0 (
    echo [OK] Backup compresso: portal_backup_%BACKUP_DATE%.zip
    rmdir /s /q "%BACKUP_DIR%"
) else (
    echo [ATTENZIONE] Compressione fallita, backup disponibile in: %BACKUP_DIR%
)

echo.
echo ===============================================
echo Dimensioni backup:
echo ===============================================
if exist "backups\portal_backup_%BACKUP_DATE%.zip" (
    dir "backups\portal_backup_%BACKUP_DATE%.zip" | findstr "portal_backup"
) else (
    dir "%BACKUP_DIR%" | findstr "File"
)

echo.
echo Backup completato!
echo.
echo Per ripristinare: scripts\restore.bat portal_backup_%BACKUP_DATE%.zip
echo.
pause 