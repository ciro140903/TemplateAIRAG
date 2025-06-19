@echo off
echo ===============================================
echo       PORTALE AZIENDALE - STATO SISTEMA
echo ===============================================
echo.

echo [STATO CONTAINERS]
docker compose ps
echo.

echo [UTILIZZO RISORSE]
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
echo.

echo [HEALTH CHECK]
echo Verifica stato servizi...
echo.

echo MongoDB:
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')" --quiet 2>nul && echo [OK] MongoDB risponde || echo [ERRORE] MongoDB non risponde

echo Redis:
docker compose exec redis redis-cli ping 2>nul && echo [OK] Redis risponde || echo [ERRORE] Redis non risponde

echo Qdrant:
curl -s -f http://localhost:6333/health >nul && echo [OK] Qdrant risponde || echo [ERRORE] Qdrant non risponde

echo Grafana:
curl -s -f http://localhost:3000/api/health >nul && echo [OK] Grafana risponde || echo [ERRORE] Grafana non risponde

echo Loki:
curl -s -f http://localhost:3100/ready >nul && echo [OK] Loki risponde || echo [ERRORE] Loki non risponde

echo.
echo [VOLUMI]
docker volume ls | findstr portal
echo.

echo [NETWORKS]
docker network ls | findstr portal
echo.

echo [LOG RECENTI]
echo Ultimi 10 eventi importanti:
docker compose logs --tail=10 2>nul | findstr -i "error\|warn\|ready\|started"
echo.

pause 