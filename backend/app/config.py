"""
Configurazione del Portale Aziendale Backend
Gestisce tutte le impostazioni dell'applicazione tramite variabili d'ambiente
"""

import os
from typing import List, Optional, Any
from pydantic import field_validator, EmailStr, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurazione principale dell'applicazione"""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ===== APPLICAZIONE =====
    app_name: str = "Portale Aziendale API"
    app_version: str = "1.0.0"
    app_description: str = "API Backend per Portale Aziendale con AI e RAG"
    debug: bool = True
    log_level: str = "INFO"
    environment: str = "development"
    
    # ===== API =====
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    frontend_url: str = "http://localhost:5173"
    
    # ===== CORS =====
    cors_origins_str: str = "http://localhost:3000,http://localhost:5173"
    cors_allow_credentials: bool = True
    cors_allow_methods_str: str = "*"
    cors_allow_headers_str: str = "*"
    
    @property
    def cors_origins(self) -> List[str]:
        """Converte la stringa CORS in lista"""
        if isinstance(self.cors_origins_str, str):
            return [origin.strip() for origin in self.cors_origins_str.split(',') if origin.strip()]
        return []
    
    @property
    def cors_allow_methods(self) -> List[str]:
        """Converte la stringa cors_allow_methods in lista"""
        if isinstance(self.cors_allow_methods_str, str):
            if self.cors_allow_methods_str == "*":
                return ["*"]
            return [method.strip() for method in self.cors_allow_methods_str.split(',') if method.strip()]
        return ["*"]
    
    @property  
    def cors_allow_headers(self) -> List[str]:
        """Converte la stringa cors_allow_headers in lista"""
        if isinstance(self.cors_allow_headers_str, str):
            if self.cors_allow_headers_str == "*":
                return ["*"]
            return [header.strip() for header in self.cors_allow_headers_str.split(',') if header.strip()]
        return ["*"]
    
    # ===== DATABASE MONGODB =====
    mongo_username: str = "admin"
    mongo_password: str = "portal_mongo_2024"
    mongo_database: str = "portal"
    mongo_host: str = "mongodb"
    mongo_port: int = 27017
    mongodb_url: Optional[str] = None
    
    @field_validator('mongodb_url', mode='before')
    @classmethod
    def build_mongodb_url(cls, v: Optional[str], info) -> str:
        if v:
            return v
        values = info.data
        return f"mongodb://{values['mongo_username']}:{values['mongo_password']}@{values['mongo_host']}:{values['mongo_port']}/{values['mongo_database']}?authSource=admin"
    
    # Configurazioni avanzate MongoDB
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    
    # ===== REDIS CACHE =====
    redis_url: str = "redis://:portal_redis_2024@redis:6379/0"
    redis_password: str = "portal_redis_2024"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    
    # ===== QDRANT VECTOR DATABASE =====
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = "portal_qdrant_2024"
    qdrant_collection_name: str = "documents"
    
    # ===== AZURE OPENAI GPT-4 =====
    azure_openai_gpt_endpoint: str = "https://YOUR_RESOURCE.openai.azure.com/"
    azure_openai_gpt_key: str = "YOUR_API_KEY"
    azure_openai_gpt_deployment: str = "gpt-4.1"
    azure_openai_gpt_api_version: str = "2024-02-15-preview"
    
    # ===== AZURE OPENAI EMBEDDING =====
    azure_openai_embedding_endpoint: str = "https://YOUR_RESOURCE.openai.azure.com/"
    azure_openai_embedding_key: str = "YOUR_API_KEY"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"
    azure_openai_embedding_api_version: str = "2024-02-15-preview"
    
    # Configurazioni AI
    ai_model_temperature: float = 0.7
    max_tokens_response: int = 2000
    rag_top_k: int = 5
    embedding_model: str = "text-embedding-3-large"
    chat_history_limit: int = 50
    
    # ===== SECURITY =====
    jwt_secret: str = "portal_jwt_super_secret_key_2024_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    encryption_key: str = "portal_encryption_key_32_chars_2024"
    secret_key: str = "portal_secret_key_for_sessions_2024"
    
    @field_validator('jwt_secret', 'encryption_key', 'secret_key')
    @classmethod
    def validate_secret_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError('Secret keys must be at least 32 characters long')
        return v
    
    # ===== RATE LIMITING =====
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # ===== FILE UPLOAD =====
    max_file_size_str: str = "100MB"
    upload_folder: str = "./uploads"
    
    @property
    def max_file_size(self) -> int:
        """Converte dimensioni file da stringa a bytes"""
        v = self.max_file_size_str.upper().strip()
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3
        }
        
        for suffix, multiplier in multipliers.items():
            if v.endswith(suffix):
                return int(float(v[:-len(suffix)]) * multiplier)
        
        return int(v)  # Assume bytes se nessun suffisso
    allowed_extensions_str: str = "pdf,docx,xlsx,txt,html,eml"
    
    @property
    def allowed_extensions(self) -> List[str]:
        """Converte la stringa allowed_extensions in lista"""
        if isinstance(self.allowed_extensions_str, str):
            return [ext.strip() for ext in self.allowed_extensions_str.split(',') if ext.strip()]
        return []
    

    
    # ===== EMAIL (opzionale) =====
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[EmailStr] = None
    
    # ===== MONITORING =====
    enable_metrics: bool = True
    metrics_port: int = 9090
    loki_url: str = "http://loki:3100"
    
    # ===== FEATURES FLAGS =====
    registration_enabled: bool = False
    mfa_enabled: bool = True
    file_upload_enabled: bool = True
    ai_chat_enabled: bool = True
    rag_enabled: bool = True
    auto_initialize_db: bool = True


# Istanza globale delle impostazioni
settings = Settings()


def get_settings() -> Settings:
    """Dependency injection per FastAPI"""
    return settings


# Configurazioni derivate per comodità
class DatabaseConfig:
    """Configurazioni specifiche per il database"""
    
    @staticmethod
    def get_mongodb_url() -> str:
        return settings.mongodb_url
    
    @staticmethod
    def get_redis_url() -> str:
        return settings.redis_url
    
    @staticmethod
    def get_qdrant_config() -> dict:
        return {
            "host": settings.qdrant_host,
            "port": settings.qdrant_port,
            "api_key": settings.qdrant_api_key,
            "collection_name": settings.qdrant_collection_name
        }


class AIConfig:
    """Configurazioni specifiche per Azure OpenAI"""
    
    @staticmethod
    def get_azure_openai_gpt_config() -> dict:
        """Configurazione per Azure OpenAI GPT-4"""
        return {
            "endpoint": settings.azure_openai_gpt_endpoint,
            "api_key": settings.azure_openai_gpt_key,
            "deployment": settings.azure_openai_gpt_deployment,
            "api_version": settings.azure_openai_gpt_api_version,
            "temperature": settings.ai_model_temperature,
            "max_tokens": settings.max_tokens_response
        }
    
    @staticmethod
    def get_azure_openai_embedding_config() -> dict:
        """Configurazione per Azure OpenAI Embedding"""
        return {
            "endpoint": settings.azure_openai_embedding_endpoint,
            "api_key": settings.azure_openai_embedding_key,
            "deployment": settings.azure_openai_embedding_deployment,
            "api_version": settings.azure_openai_embedding_api_version
        }
    
    @staticmethod
    def is_gpt_configured() -> bool:
        """Verifica se Azure OpenAI GPT è configurato correttamente"""
        return (
            settings.azure_openai_gpt_endpoint != "https://YOUR_RESOURCE.openai.azure.com/"
            and settings.azure_openai_gpt_key != "YOUR_API_KEY"
            and len(settings.azure_openai_gpt_key) > 10
        )
    
    @staticmethod
    def is_embedding_configured() -> bool:
        """Verifica se Azure OpenAI Embedding è configurato correttamente"""
        return (
            settings.azure_openai_embedding_endpoint != "https://YOUR_RESOURCE.openai.azure.com/"
            and settings.azure_openai_embedding_key != "YOUR_API_KEY"
            and len(settings.azure_openai_embedding_key) > 10
        )


# Istanze globali per configurazioni specifiche
db_config = DatabaseConfig()
ai_config = AIConfig() 