"""
API Routes per pannello amministrativo
Gestione configurazioni sistema, monitoraggio, statistiche
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
import structlog
from bson import ObjectId

from app.core import get_mongodb
from app.models import (
    ConfigResponse,
    ConfigCreate,
    ConfigUpdate,
    UserRole,
    config_helper,
    PyObjectId
)
from app.api.v1.auth import get_current_user
from app.core.database_init import check_database_health

# Logger
logger = structlog.get_logger(__name__)

# Router
router = APIRouter()


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency per verificare che l'utente sia admin"""
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso riservato agli amministratori"
        )
    return current_user


# ===== CONFIGURAZIONI SISTEMA =====

@router.get("/config", response_model=List[ConfigResponse])
async def get_system_configs(
    category: Optional[str] = Query(None, description="Filtra per categoria"),
    is_public: Optional[bool] = Query(None, description="Filtra per visibilità pubblica"),
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Ottieni configurazioni di sistema"""
    
    try:
        # Costruisci filtro
        filter_query = {}
        
        if category:
            filter_query["category"] = category
        if is_public is not None:
            filter_query["is_public"] = is_public
        
        # Recupera configurazioni
        cursor = mongodb.system_config.find(filter_query)
        configs = await cursor.to_list(length=None)
        
        # Converti in response
        config_responses = [ConfigResponse(**config_helper(config)) for config in configs]
        
        logger.info(
            "Configurazioni sistema recuperate",
            admin_id=str(current_user["_id"]),
            count=len(config_responses),
            category=category
        )
        
        return config_responses
        
    except Exception as e:
        logger.error("Errore recupero configurazioni", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/config", response_model=ConfigResponse)
async def create_system_config(
    config_data: ConfigCreate,
    request: Request,
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Crea nuova configurazione sistema"""
    
    try:
        # Verifica che la chiave non esista già
        existing = await mongodb.system_config.find_one({"key": config_data.key})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configurazione con questa chiave già esistente"
            )
        
        # Crea configurazione
        now = datetime.utcnow()
        config_doc = {
            **config_data.model_dump(),
            "created_at": now,
            "updated_at": now,
            "created_by": current_user["_id"]
        }
        
        result = await mongodb.system_config.insert_one(config_doc)
        
        # Recupera configurazione creata
        created_config = await mongodb.system_config.find_one({"_id": result.inserted_id})
        
        # Log evento
        from app.core.advanced_logging import log_security_event
        await log_security_event(
            user_id=str(current_user["_id"]),
            action="config_created",
            details={"key": config_data.key, "category": config_data.category},
            ip_address=request.client.host if request.client else None,
            severity="info"
        )
        
        logger.info(
            "Configurazione sistema creata",
            admin_id=str(current_user["_id"]),
            config_key=config_data.key,
            category=config_data.category
        )
        
        return ConfigResponse(**config_helper(created_config))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore creazione configurazione", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.put("/config/{config_key}", response_model=ConfigResponse)
async def update_system_config(
    config_key: str,
    config_update: ConfigUpdate,
    request: Request,
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Aggiorna configurazione sistema"""
    
    try:
        # Trova configurazione
        config = await mongodb.system_config.find_one({"key": config_key})
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configurazione non trovata"
            )
        
        # Verifica se modificabile
        if not config.get("is_editable", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configurazione non modificabile"
            )
        
        # Prepara aggiornamento
        update_fields = {
            "updated_at": datetime.utcnow(),
            "last_modified_by": current_user["_id"]
        }
        
        # Aggiorna solo campi forniti
        update_data = config_update.model_dump(exclude_unset=True)
        update_fields.update(update_data)
        
        # Aggiorna database
        result = await mongodb.system_config.update_one(
            {"key": config_key},
            {"$set": update_fields}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessuna modifica effettuata"
            )
        
        # Recupera configurazione aggiornata
        updated_config = await mongodb.system_config.find_one({"key": config_key})
        
        # Log evento
        from app.core.advanced_logging import log_security_event
        await log_security_event(
            user_id=str(current_user["_id"]),
            action="config_updated",
            details={
                "key": config_key,
                "fields": list(update_data.keys()),
                "requires_restart": config.get("requires_restart", False)
            },
            ip_address=request.client.host if request.client else None,
            severity="info"
        )
        
        logger.info(
            "Configurazione sistema aggiornata",
            admin_id=str(current_user["_id"]),
            config_key=config_key,
            fields=list(update_data.keys())
        )
        
        return ConfigResponse(**config_helper(updated_config))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore aggiornamento configurazione", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.delete("/config/{config_key}")
async def delete_system_config(
    config_key: str,
    request: Request,
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Elimina configurazione sistema"""
    
    try:
        # Trova configurazione
        config = await mongodb.system_config.find_one({"key": config_key})
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configurazione non trovata"
            )
        
        # Verifica se eliminabile
        if not config.get("is_editable", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configurazione non eliminabile"
            )
        
        # Elimina configurazione
        await mongodb.system_config.delete_one({"key": config_key})
        
        # Log evento
        from app.core.advanced_logging import log_security_event
        await log_security_event(
            user_id=str(current_user["_id"]),
            action="config_deleted",
            details={"key": config_key, "category": config.get("category")},
            ip_address=request.client.host if request.client else None,
            severity="warning"
        )
        
        logger.info(
            "Configurazione sistema eliminata",
            admin_id=str(current_user["_id"]),
            config_key=config_key
        )
        
        return {"message": "Configurazione eliminata con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore eliminazione configurazione", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


# ===== MONITORAGGIO E STATISTICHE =====

@router.get("/stats/overview")
async def get_system_overview(
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Ottieni panoramica statistiche sistema"""
    
    try:
        # Statistiche utenti
        total_users = await mongodb.users.count_documents({})
        active_users = await mongodb.users.count_documents({"is_active": True})
        admin_users = await mongodb.users.count_documents({"role": {"$in": ["admin", "super_admin"]}})
        
        # Statistiche chat
        total_sessions = await mongodb.chat_sessions.count_documents({})
        active_sessions = await mongodb.chat_sessions.count_documents({"is_active": True})
        total_messages = await mongodb.chat_messages.count_documents({})
        
        # Statistiche ultimi 30 giorni
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        new_users_30d = await mongodb.users.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        new_sessions_30d = await mongodb.chat_sessions.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        messages_30d = await mongodb.chat_messages.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Statistiche oggi
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        active_users_today = await mongodb.users.count_documents({
            "last_login": {"$gte": today_start}
        })
        
        messages_today = await mongodb.chat_messages.count_documents({
            "created_at": {"$gte": today_start}
        })
        
        # Health check database
        db_health = await check_database_health(mongodb.client.get_database())
        
        overview = {
            "users": {
                "total": total_users,
                "active": active_users,
                "admins": admin_users,
                "new_30d": new_users_30d,
                "active_today": active_users_today
            },
            "chat": {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_messages": total_messages,
                "new_sessions_30d": new_sessions_30d,
                "messages_30d": messages_30d,
                "messages_today": messages_today
            },
            "system": {
                "database_health": db_health["status"],
                "collections": db_health.get("collections", {}),
                "uptime": "Sistema attivo"  # Implementare calcolo uptime
            }
        }
        
        logger.info(
            "Statistiche sistema recuperate",
            admin_id=str(current_user["_id"]),
            total_users=total_users,
            total_sessions=total_sessions
        )
        
        return overview
        
    except Exception as e:
        logger.error("Errore recupero statistiche", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.get("/stats/usage")
async def get_usage_stats(
    days: int = Query(7, ge=1, le=90, description="Giorni di statistiche"),
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Ottieni statistiche utilizzo per periodo"""
    
    try:
        # Calcola periodo
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Pipeline aggregazione per statistiche giornaliere
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"},
                        "day": {"$dayOfMonth": "$created_at"}
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        # Statistiche messaggi
        message_stats = await mongodb.chat_messages.aggregate(pipeline).to_list(length=None)
        
        # Statistiche sessioni
        session_stats = await mongodb.chat_sessions.aggregate(pipeline).to_list(length=None)
        
        # Statistiche utenti attivi (login)
        user_pipeline = [
            {
                "$match": {
                    "last_login": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$last_login"},
                        "month": {"$month": "$last_login"},
                        "day": {"$dayOfMonth": "$last_login"}
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        user_stats = await mongodb.users.aggregate(user_pipeline).to_list(length=None)
        
        # Formatta risultati
        def format_stats(stats_data):
            return [
                {
                    "date": f"{item['_id']['year']}-{item['_id']['month']:02d}-{item['_id']['day']:02d}",
                    "count": item["count"]
                }
                for item in stats_data
            ]
        
        usage_stats = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "messages": format_stats(message_stats),
            "sessions": format_stats(session_stats),
            "active_users": format_stats(user_stats)
        }
        
        logger.info(
            "Statistiche utilizzo recuperate",
            admin_id=str(current_user["_id"]),
            days=days,
            message_points=len(message_stats),
            session_points=len(session_stats)
        )
        
        return usage_stats
        
    except Exception as e:
        logger.error("Errore recupero statistiche utilizzo", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.get("/health/detailed")
async def get_detailed_health(
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Ottieni health check dettagliato del sistema"""
    
    try:
        # Health check database
        db_health = await check_database_health(mongodb.client.get_database())
        
        # Verifica servizi esterni (simulato)
        services_health = {
            "mongodb": db_health["status"] == "healthy",
            "redis": True,  # Implementare check Redis
            "azure_openai": True,  # Implementare check Azure OpenAI
            "qdrant": True  # Implementare check Qdrant
        }
        
        # Statistiche performance recenti
        recent_errors = await mongodb.security_events.count_documents({
            "severity": {"$in": ["error", "critical"]},
            "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=1)}
        })
        
        detailed_health = {
            "status": "healthy" if all(services_health.values()) else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_health,
            "database": db_health,
            "performance": {
                "recent_errors": recent_errors,
                "avg_response_time": "< 200ms",  # Implementare calcolo reale
                "memory_usage": "65%"  # Implementare monitoraggio reale
            }
        }
        
        logger.info(
            "Health check dettagliato eseguito",
            admin_id=str(current_user["_id"]),
            status=detailed_health["status"],
            recent_errors=recent_errors
        )
        
        return detailed_health
        
    except Exception as e:
        logger.error("Errore health check dettagliato", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        ) 