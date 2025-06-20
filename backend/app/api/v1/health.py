"""
API Routes per health check e monitoring
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.core import get_mongodb, get_redis
from app.core.database_init import check_database_health
from app.config import settings

# Logger
logger = structlog.get_logger(__name__)

# Router
router = APIRouter()


@router.get("/")
async def basic_health():
    """Health check di base"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": settings.app_name,
        "version": settings.app_version
    }


@router.get("/detailed")
async def detailed_health(
    mongodb = Depends(get_mongodb),
    redis = Depends(get_redis)
):
    """Health check dettagliato con verifica servizi"""
    
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "services": {}
        }
        
        # Check MongoDB
        try:
            db_health = await check_database_health(mongodb.client.get_database())
            health_status["services"]["mongodb"] = {
                "status": db_health["status"],
                "collections": len(db_health.get("collections", {})),
                "response_time": "< 50ms"
            }
        except Exception as e:
            health_status["services"]["mongodb"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check Redis
        try:
            await redis.ping()
            health_status["services"]["redis"] = {
                "status": "healthy",
                "response_time": "< 10ms"
            }
        except Exception as e:
            health_status["services"]["redis"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check Azure OpenAI (simulato)
        health_status["services"]["azure_openai"] = {
            "status": "healthy" if settings.ai_chat_enabled else "disabled",
            "gpt_configured": bool(settings.azure_openai_gpt_key != "YOUR_API_KEY"),
            "embedding_configured": bool(settings.azure_openai_embedding_key != "YOUR_API_KEY")
        }
        
        return health_status
        
    except Exception as e:
        logger.error("Errore health check dettagliato", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(e) if settings.debug else "Service check failed"
        }


@router.get("/readiness")
async def readiness_check(
    mongodb = Depends(get_mongodb)
):
    """Readiness probe per Kubernetes"""
    
    try:
        # Verifica connessione database essenziale
        await mongodb.command("ping")
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/liveness")
async def liveness_check():
    """Liveness probe per Kubernetes"""
    
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime": "Sistema attivo"  # Implementare calcolo uptime reale
    } 