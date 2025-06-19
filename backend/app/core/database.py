"""
Database connections per MongoDB e Redis
Gestisce le connessioni asincrone ai database del sistema
"""

import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis
import pymongo
from pymongo import MongoClient
import structlog

from app.config import settings

# Logger strutturato
logger = structlog.get_logger(__name__)


class MongoDBManager:
    """Manager per la connessione MongoDB con Motor (async)"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.sync_client: Optional[MongoClient] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Stabilisce la connessione a MongoDB"""
        try:
            logger.info("Connessione a MongoDB...", url=settings.mongodb_url.replace(settings.mongo_password, "***"))
            
            # Client asincrono (principale)
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                maxPoolSize=settings.db_pool_size,
                maxIdleTimeMS=settings.db_pool_timeout * 1000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=0,
                retryWrites=True,
                w="majority"
            )
            
            # Test connessione
            await self.client.admin.command('ping')
            
            # Database instance
            self.database = self.client[settings.mongo_database]
            
            # Client sincrono per operazioni che lo richiedono
            self.sync_client = MongoClient(
                settings.mongodb_url,
                maxPoolSize=10,
                serverSelectionTimeoutMS=5000
            )
            
            self._connected = True
            logger.info("✅ MongoDB connesso con successo")
            
        except Exception as e:
            logger.error("❌ Errore connessione MongoDB", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Chiude la connessione a MongoDB"""
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnesso")
        
        if self.sync_client:
            self.sync_client.close()
            logger.info("MongoDB sync client disconnesso")
        
        self._connected = False
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Ritorna l'istanza del database"""
        if not self._connected or not self.database:
            raise RuntimeError("MongoDB non connesso")
        return self.database
    
    def get_sync_client(self) -> MongoClient:
        """Ritorna il client sincrono per operazioni specifiche"""
        if not self._connected or not self.sync_client:
            raise RuntimeError("MongoDB sync client non connesso")
        return self.sync_client
    
    async def health_check(self) -> bool:
        """Controlla lo stato della connessione"""
        try:
            await self.client.admin.command('ping')
            return True
        except:
            return False
    
    # Metodi di utilità per le collezioni
    def get_collection(self, name: str):
        """Ritorna una collezione specifica"""
        return self.get_database()[name]
    
    @property
    def users(self):
        return self.get_collection("users")
    
    @property
    def chat_sessions(self):
        return self.get_collection("chat_sessions")
    
    @property
    def chat_messages(self):
        return self.get_collection("chat_messages")
    
    @property
    def documents(self):
        return self.get_collection("documents")
    
    @property
    def document_chunks(self):
        return self.get_collection("document_chunks")
    
    @property
    def indexing_jobs(self):
        return self.get_collection("indexing_jobs")
    
    @property
    def system_config(self):
        return self.get_collection("system_config")
    
    @property
    def audit_logs(self):
        return self.get_collection("audit_logs")
    
    @property
    def api_keys(self):
        return self.get_collection("api_keys")
    
    @property
    def user_sessions(self):
        return self.get_collection("user_sessions")


class RedisManager:
    """Manager per la connessione Redis"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Stabilisce la connessione a Redis"""
        try:
            logger.info("Connessione a Redis...", host=settings.redis_host, port=settings.redis_port)
            
            self.client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            
            # Test connessione
            await self.client.ping()
            
            self._connected = True
            logger.info("✅ Redis connesso con successo")
            
        except Exception as e:
            logger.error("❌ Errore connessione Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Chiude la connessione a Redis"""
        if self.client:
            await self.client.close()
            logger.info("Redis disconnesso")
        self._connected = False
    
    def get_client(self) -> redis.Redis:
        """Ritorna il client Redis"""
        if not self._connected or not self.client:
            raise RuntimeError("Redis non connesso")
        return self.client
    
    async def health_check(self) -> bool:
        """Controlla lo stato della connessione"""
        try:
            await self.client.ping()
            return True
        except:
            return False
    
    # Metodi di utilità per operazioni comuni
    async def set_cache(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Imposta un valore in cache"""
        try:
            result = await self.client.set(key, value, ex=expire)
            return result
        except Exception as e:
            logger.error("Errore set cache", key=key, error=str(e))
            return False
    
    async def get_cache(self, key: str) -> Optional[str]:
        """Recupera un valore dalla cache"""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error("Errore get cache", key=key, error=str(e))
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """Elimina un valore dalla cache"""
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.error("Errore delete cache", key=key, error=str(e))
            return False
    
    async def set_session(self, session_id: str, data: str, expire: int = 3600) -> bool:
        """Imposta dati di sessione"""
        return await self.set_cache(f"session:{session_id}", data, expire)
    
    async def get_session(self, session_id: str) -> Optional[str]:
        """Recupera dati di sessione"""
        return await self.get_cache(f"session:{session_id}")
    
    async def delete_session(self, session_id: str) -> bool:
        """Elimina dati di sessione"""
        return await self.delete_cache(f"session:{session_id}")
    
    async def blacklist_token(self, token_id: str, expire: int = None) -> bool:
        """Aggiunge un token JWT alla blacklist"""
        if expire is None:
            expire = settings.jwt_access_token_expire_minutes * 60
        return await self.set_cache(f"blacklist:{token_id}", "1", expire)
    
    async def is_token_blacklisted(self, token_id: str) -> bool:
        """Controlla se un token è in blacklist"""
        result = await self.get_cache(f"blacklist:{token_id}")
        return result is not None


# Istanze globali dei manager
mongodb_manager = MongoDBManager()
redis_manager = RedisManager()


async def connect_databases() -> None:
    """Connette tutti i database"""
    logger.info("🔌 Inizializzazione connessioni database...")
    
    try:
        # Connessione MongoDB
        await mongodb_manager.connect()
        
        # Connessione Redis  
        await redis_manager.connect()
        
        logger.info("✅ Tutti i database connessi con successo")
        
    except Exception as e:
        logger.error("❌ Errore inizializzazione database", error=str(e))
        raise


async def disconnect_databases() -> None:
    """Disconnette tutti i database"""
    logger.info("🔌 Chiusura connessioni database...")
    
    try:
        await mongodb_manager.disconnect()
        await redis_manager.disconnect()
        logger.info("✅ Tutti i database disconnessi")
        
    except Exception as e:
        logger.error("❌ Errore chiusura database", error=str(e))


async def health_check_databases() -> dict:
    """Controlla lo stato di tutti i database"""
    return {
        "mongodb": await mongodb_manager.health_check(),
        "redis": await redis_manager.health_check()
    }


# Dependency injection per FastAPI
def get_mongodb() -> AsyncIOMotorDatabase:
    """Dependency per ottenere il database MongoDB"""
    return mongodb_manager.get_database()


def get_redis() -> redis.Redis:
    """Dependency per ottenere il client Redis"""
    return redis_manager.get_client()


# Funzioni di utilità per testing
async def reset_test_database():
    """Resetta il database per i test (solo in ambiente test)"""
    if settings.environment != "test":
        raise RuntimeError("Reset database consentito solo in ambiente test")
    
    db = mongodb_manager.get_database()
    
    # Elimina tutte le collezioni tranne system_config
    collections = await db.list_collection_names()
    for collection_name in collections:
        if collection_name != "system_config":
            await db[collection_name].delete_many({})
    
    # Pulisce Redis
    redis_client = redis_manager.get_client()
    await redis_client.flushdb()
    
    logger.info("Database test resettato")


if __name__ == "__main__":
    # Test delle connessioni
    async def test_connections():
        await connect_databases()
        health = await health_check_databases()
        print("Health check:", health)
        await disconnect_databases()
    
    asyncio.run(test_connections()) 