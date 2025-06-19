@echo off
REM ====================
REM PORTALE AZIENDALE - INFORMAZIONI SERVIZI
REM ====================
REM Tutti i servizi Docker sono sul server 172.16.1.50
REM Questo script mostra solo le informazioni

echo.
echo ========================================
echo   PORTALE AZIENDALE - SERVIZI REMOTI
echo ========================================
echo.

cd /d "%~dp0.."

echo [INFO] Controllo file di configurazione...
if not exist ".env" (
    echo [ERRORE] File .env non trovato!
    echo [INFO] Copia .env.example in .env e configura i valori
    pause
    exit /b 1
)

echo [INFO] Configurazione verificata!
echo.
echo ========================================
echo   SERVIZI DISPONIBILI (172.16.1.50)
echo ========================================
echo.
echo MongoDB:     172.16.1.50:27017
echo Redis:       172.16.1.50:6379  
echo Qdrant:      172.16.1.50:6333
echo Grafana:     http://172.16.1.50:3000
echo Loki:        http://172.16.1.50:3100
echo.
echo ========================================
echo   AVVIO BACKEND E FRONTEND
echo ========================================
echo.
echo 1. Backend (nuovo terminale):
echo    cd backend
echo    poetry install
echo    poetry run uvicorn app.main:app --reload
echo.
echo 2. Frontend (nuovo terminale):
echo    cd frontend
echo    npm install
echo    npm run dev
echo.
echo ========================================
echo   ACCESSO
echo ========================================
echo.
echo Backend API:  http://localhost:8000
echo Frontend:     http://localhost:5173
echo Docs API:     http://localhost:8000/docs
echo.
echo ========================================
echo.
pause 