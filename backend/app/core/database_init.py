"""
Inizializzazione database MongoDB
Crea indici e dati di default secondo specifiche Fase 02
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.config import settings
from app.models import UserRole, UserInDB
from app.core.security import get_password_hash

logger = structlog.get_logger(__name__)


async def create_indexes(db: AsyncIOMotorDatabase) -> Dict[str, bool]:
    """
    Crea tutti gli indici necessari per le collezioni
    
    Returns:
        Dict con risultati creazione indici
    """
    results = {}
    
    try:
        # ===== INDICI COLLEZIONE USERS =====
        
        # Indice univoco per email
        await db.users.create_index("email", unique=True, name="idx_users_email_unique")
        results["users_email"] = True
        
        # Indice univoco per username
        await db.users.create_index("username", unique=True, name="idx_users_username_unique")
        results["users_username"] = True
        
        # Indice composto per query frequenti
        await db.users.create_index([
            ("is_active", 1),
            ("role", 1),
            ("created_at", -1)
        ], name="idx_users_active_role_created")
        results["users_compound"] = True
        
        # Indice per ricerca testo
        await db.users.create_index([
            ("first_name", "text"),
            ("last_name", "text"),
            ("email", "text"),
            ("username", "text")
        ], name="idx_users_text_search")
        results["users_text"] = True
        
        
        # ===== INDICI COLLEZIONE CHAT_SESSIONS =====
        
        # Indice composto per sessioni utente
        await db.chat_sessions.create_index([
            ("user_id", 1),
            ("is_active", 1),
            ("updated_at", -1)
        ], name="idx_sessions_user_active_updated")
        results["sessions_user"] = True
        
        # Indice per sessioni archiviate
        await db.chat_sessions.create_index([
            ("user_id", 1),
            ("is_archived", 1),
            ("created_at", -1)
        ], name="idx_sessions_user_archived_created")
        results["sessions_archived"] = True
        
        # Indice per sessioni pinnate
        await db.chat_sessions.create_index([
            ("user_id", 1),
            ("is_pinned", 1)
        ], name="idx_sessions_user_pinned")
        results["sessions_pinned"] = True
        
        # Indice per ricerca per tag
        await db.chat_sessions.create_index("tags", name="idx_sessions_tags")
        results["sessions_tags"] = True
        
        
        # ===== INDICI COLLEZIONE CHAT_MESSAGES =====
        
        # Indice composto per messaggi per sessione
        await db.chat_messages.create_index([
            ("session_id", 1),
            ("created_at", 1)
        ], name="idx_messages_session_created")
        results["messages_session"] = True
        
        # Indice per messaggi utente
        await db.chat_messages.create_index([
            ("user_id", 1),
            ("created_at", -1)
        ], name="idx_messages_user_created")
        results["messages_user"] = True
        
        # Indice per tipo messaggio
        await db.chat_messages.create_index([
            ("session_id", 1),
            ("message_type", 1),
            ("created_at", 1)
        ], name="idx_messages_session_type_created")
        results["messages_type"] = True
        
        # Indice per status messaggio
        await db.chat_messages.create_index("status", name="idx_messages_status")
        results["messages_status"] = True
        
        
        # ===== INDICI COLLEZIONE SYSTEM_CONFIG =====
        
        # Indice univoco per chiave configurazione
        await db.system_config.create_index("key", unique=True, name="idx_config_key_unique")
        results["config_key"] = True
        
        # Indice per categoria
        await db.system_config.create_index([
            ("category", 1),
            ("key", 1)
        ], name="idx_config_category_key")
        results["config_category"] = True
        
        # Indice per configurazioni pubbliche
        await db.system_config.create_index("is_public", name="idx_config_public")
        results["config_public"] = True
        
        
        # ===== INDICI COLLEZIONE AI_MODEL_CONFIG =====
        
        # Indice per nome modello
        await db.ai_model_config.create_index("model_name", name="idx_ai_model_name")
        results["ai_model_name"] = True
        
        # Indice per provider e tipo
        await db.ai_model_config.create_index([
            ("provider", 1),
            ("model_type", 1),
            ("is_active", 1)
        ], name="idx_ai_model_provider_type_active")
        results["ai_model_provider"] = True
        
        # Indice per modello default
        await db.ai_model_config.create_index([
            ("model_type", 1),
            ("is_default", 1)
        ], name="idx_ai_model_type_default")
        results["ai_model_default"] = True
        
        
        # ===== INDICI COLLEZIONE SECURITY_EVENTS =====
        
        # Indice per eventi utente
        await db.security_events.create_index([
            ("user_id", 1),
            ("timestamp", -1)
        ], name="idx_security_user_timestamp")
        results["security_user"] = True
        
        # Indice per azione e severità
        await db.security_events.create_index([
            ("action", 1),
            ("severity", 1),
            ("timestamp", -1)
        ], name="idx_security_action_severity_timestamp")
        results["security_action"] = True
        
        # Indice per IP address
        await db.security_events.create_index("ip_address", name="idx_security_ip")
        results["security_ip"] = True
        
        # Indice TTL per pulizia automatica (90 giorni)
        await db.security_events.create_index(
            "timestamp",
            expireAfterSeconds=90 * 24 * 60 * 60,  # 90 giorni in secondi
            name="idx_security_ttl"
        )
        results["security_ttl"] = True
        
        
        logger.info("Indici database creati con successo", results=results)
        return results
        
    except Exception as e:
        logger.error("Errore creazione indici database", error=str(e))
        raise


async def create_default_admin(db: AsyncIOMotorDatabase) -> bool:
    """
    Crea utente admin di default se non esiste
    
    Returns:
        True se creato, False se già esistente
    """
    try:
        # Verifica se esiste già un super admin
        existing_admin = await db.users.find_one({"role": UserRole.SUPER_ADMIN.value})
        
        if existing_admin:
            logger.info("Super admin già esistente", admin_id=str(existing_admin["_id"]))
            return False
        
        # Crea super admin di default
        now = datetime.utcnow()
        admin_data = {
            "username": "admin",
            "email": "admin@portal.local",
            "first_name": "Super",
            "last_name": "Admin",
            "password_hash": get_password_hash("admin123!"),  # Password temporanea
            "role": UserRole.SUPER_ADMIN.value,
            "is_active": True,
            "is_verified": True,
            "created_at": now,
            "updated_at": now,
            "password_changed_at": now,
            "login_count": 0,
            "failed_login_attempts": 0,
            "settings": {
                "theme": "light",
                "language": "it",
                "notifications": True,
                "chat_history_visible": True,
                "auto_save_documents": True,
                "default_ai_temperature": 0.7
            },
            "mfa": {
                "enabled": False,
                "secret": None,
                "backup_codes": [],
                "last_used": None,
                "setup_completed": False
            }
        }
        
        result = await db.users.insert_one(admin_data)
        
        logger.info(
            "Super admin creato",
            admin_id=str(result.inserted_id),
            username="admin",
            email="admin@portal.local"
        )
        
        logger.warning(
            "IMPORTANTE: Cambiare la password dell'admin di default!",
            username="admin",
            default_password="admin123!"
        )
        
        return True
        
    except Exception as e:
        logger.error("Errore creazione admin di default", error=str(e))
        raise


async def create_default_config(db: AsyncIOMotorDatabase) -> Dict[str, bool]:
    """
    Crea configurazioni di sistema di default
    
    Returns:
        Dict con risultati creazione configurazioni
    """
    results = {}
    
    try:
        default_configs = [
            # Configurazioni AI
            {
                "key": "ai_default_temperature",
                "category": "ai",
                "config_type": "float",
                "value": 0.7,
                "default_value": 0.7,
                "description": "Temperatura predefinita per le risposte AI",
                "is_public": True,
                "is_editable": True,
                "requires_restart": False,
                "validation_rules": {"min": 0.0, "max": 1.0}
            },
            {
                "key": "ai_max_tokens",
                "category": "ai",
                "config_type": "integer",
                "value": 2000,
                "default_value": 2000,
                "description": "Numero massimo di token per risposta AI",
                "is_public": True,
                "is_editable": True,
                "requires_restart": False,
                "validation_rules": {"min": 100, "max": 8000}
            },
            {
                "key": "rag_top_k",
                "category": "ai",
                "config_type": "integer",
                "value": 5,
                "default_value": 5,
                "description": "Numero di documenti RAG da utilizzare",
                "is_public": False,
                "is_editable": True,
                "requires_restart": False,
                "validation_rules": {"min": 1, "max": 20}
            },
            
            # Configurazioni Security
            {
                "key": "max_login_attempts",
                "category": "security",
                "config_type": "integer",
                "value": 5,
                "default_value": 5,
                "description": "Numero massimo di tentativi di login falliti",
                "is_public": False,
                "is_editable": True,
                "requires_restart": False,
                "validation_rules": {"min": 3, "max": 10}
            },
            {
                "key": "lockout_duration_minutes",
                "category": "security",
                "config_type": "integer",
                "value": 15,
                "default_value": 15,
                "description": "Durata blocco account in minuti",
                "is_public": False,
                "is_editable": True,
                "requires_restart": False,
                "validation_rules": {"min": 5, "max": 60}
            },
            
            # Configurazioni System
            {
                "key": "maintenance_mode",
                "category": "system",
                "config_type": "boolean",
                "value": False,
                "default_value": False,
                "description": "Modalità manutenzione attiva",
                "is_public": True,
                "is_editable": True,
                "requires_restart": False
            },
            {
                "key": "registration_enabled",
                "category": "features",
                "config_type": "boolean",
                "value": False,
                "default_value": False,
                "description": "Registrazione nuovi utenti abilitata",
                "is_public": True,
                "is_editable": True,
                "requires_restart": False
            }
        ]
        
        for config in default_configs:
            # Verifica se configurazione esiste già
            existing = await db.system_config.find_one({"key": config["key"]})
            
            if not existing:
                config["created_at"] = datetime.utcnow()
                config["updated_at"] = datetime.utcnow()
                
                await db.system_config.insert_one(config)
                results[config["key"]] = True
                
                logger.info("Configurazione creata", key=config["key"])
            else:
                results[config["key"]] = False
        
        return results
        
    except Exception as e:
        logger.error("Errore creazione configurazioni di default", error=str(e))
        raise


async def initialize_database(db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """
    Inizializza completamente il database
    
    Returns:
        Dict con risultati inizializzazione
    """
    logger.info("Inizio inizializzazione database")
    
    results = {
        "indexes": {},
        "admin_created": False,
        "configs": {},
        "success": False
    }
    
    try:
        # Crea indici
        logger.info("Creazione indici database...")
        results["indexes"] = await create_indexes(db)
        
        # Crea admin di default
        logger.info("Creazione admin di default...")
        results["admin_created"] = await create_default_admin(db)
        
        # Crea configurazioni di default
        logger.info("Creazione configurazioni di default...")
        results["configs"] = await create_default_config(db)
        
        results["success"] = True
        
        logger.info(
            "Inizializzazione database completata",
            indexes_created=len([k for k, v in results["indexes"].items() if v]),
            admin_created=results["admin_created"],
            configs_created=len([k for k, v in results["configs"].items() if v])
        )
        
        return results
        
    except Exception as e:
        logger.error("Errore inizializzazione database", error=str(e))
        results["error"] = str(e)
        raise


async def check_database_health(db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """
    Verifica salute del database
    
    Returns:
        Dict con stato salute database
    """
    health = {
        "status": "unknown",
        "collections": {},
        "indexes": {},
        "stats": {}
    }
    
    try:
        # Verifica connessione
        await db.command("ping")
        
        # Verifica collezioni principali
        collections = ["users", "chat_sessions", "chat_messages", "system_config"]
        
        for collection_name in collections:
            collection = db[collection_name]
            
            # Conta documenti
            count = await collection.count_documents({})
            health["collections"][collection_name] = {
                "exists": True,
                "document_count": count
            }
            
            # Verifica indici
            indexes = await collection.list_indexes().to_list(length=None)
            health["indexes"][collection_name] = len(indexes)
        
        # Statistiche database
        stats = await db.command("dbStats")
        health["stats"] = {
            "data_size": stats.get("dataSize", 0),
            "storage_size": stats.get("storageSize", 0),
            "index_size": stats.get("indexSize", 0),
            "collections": stats.get("collections", 0)
        }
        
        health["status"] = "healthy"
        
    except Exception as e:
        health["status"] = "unhealthy"
        health["error"] = str(e)
        logger.error("Database health check failed", error=str(e))
    
    return health 