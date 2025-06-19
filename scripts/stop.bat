@echo off
echo ===============================================
echo       PORTALE AZIENDALE - ARRESTO SISTEMA
echo ===============================================
echo.

echo [1/3] Arresto servizi applicazione...
docker compose stop backend frontend 2>nul

echo [2/3] Arresto servizi infrastrutturali...
docker compose stop nginx-proxy-manager grafana loki promtail

echo [3/3] Arresto database...
docker compose stop mongodb redis qdrant

echo.
echo Tutti i servizi sono stati arrestati.
echo.
echo Per un arresto completo con rimozione: docker compose down
echo Per rimuovere anche i volumi: docker compose down -v
echo Per un reset completo: scripts\reset.bat
echo.
pause 