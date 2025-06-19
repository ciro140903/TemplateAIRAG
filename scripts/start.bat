@echo off
echo ===============================================
echo        PORTALE AZIENDALE - AVVIO SISTEMA
echo ===============================================
echo.

REM Verifica che Docker sia installato
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRORE: Docker non è installato o non è nel PATH
    echo Installa Docker Desktop e riprova
    pause
    exit /b 1
)

REM Verifica che Docker Compose sia disponibile
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRORE: Docker Compose non è disponibile
    echo Aggiorna Docker Desktop alla versione più recente
    pause
    exit /b 1
)

echo [1/6] Verifica configurazione...
if not exist ".env" (
    echo ERRORE: File .env non trovato
    echo Copia .env.example in .env e configuralo
    pause
    exit /b 1
)

echo [2/6] Creazione network...
docker network create portal_network 2>nul

echo [3/6] Creazione directory dati...
if not exist "data\mongodb" mkdir "data\mongodb"
if not exist "data\qdrant" mkdir "data\qdrant"
if not exist "data\redis" mkdir "data\redis"
if not exist "data\loki" mkdir "data\loki"
if not exist "logs" mkdir "logs"
if not exist "uploads" mkdir "uploads"
if not exist "nginx\data" mkdir "nginx\data"
if not exist "nginx\letsencrypt" mkdir "nginx\letsencrypt"

echo [4/6] Controllo permessi...
REM Su Windows normalmente non ci sono problemi di permessi come su Linux

echo [5/6] Avvio servizi infrastrutturali...
echo Avvio database e monitoring...
docker compose up -d mongodb redis qdrant
echo Attendo che i database siano pronti...
timeout /t 10 /nobreak >nul

docker compose up -d loki promtail grafana
echo Attendo che il monitoring sia pronto...
timeout /t 15 /nobreak >nul

echo [6/6] Avvio proxy manager...
docker compose up -d nginx-proxy-manager

echo.
echo ===============================================
echo        AVVIO COMPLETATO!
echo ===============================================
echo.
echo Servizi disponibili:
echo - MongoDB:               localhost:27017
echo - Redis:                 localhost:6379
echo - Qdrant:                localhost:6333
echo - Grafana:               http://localhost:3000
echo - Nginx Proxy Manager:   http://localhost:81
echo - Loki:                  http://localhost:3100
echo.
echo Credenziali di default:
echo - Grafana:       admin / portal_grafana_2024
echo - MongoDB:       admin / portal_mongo_2024
echo - Nginx Proxy:   admin@example.com / changeme
echo.
echo Per verificare lo stato: docker compose ps
echo Per vedere i log: docker compose logs -f [servizio]
echo Per fermare tutto: scripts\stop.bat
echo.
pause 