"""
Applicazione FastAPI principale del Portale Aziendale
Entry point per l'API backend
"""

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog
from contextlib import asynccontextmanager

from app.config import settings
from app.core import (
    connect_databases, 
    disconnect_databases, 
    health_check_databases,
    setup_logging,
    log_api_call
)
from app.core.advanced_logging import (
    setup_structured_logging,
    log_startup_info,
    log_shutdown_info,
    PerformanceTracker
)
from app.core.database_init import initialize_database

# Setup logging strutturato prima di tutto
setup_structured_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestisce startup e shutdown dell'applicazione"""
    # Startup
    await log_startup_info()
    
    try:
        # Connessione ai database
        with PerformanceTracker("database_connection"):
            await connect_databases()
        
        # Inizializzazione database (indici, admin, config)
        if settings.auto_initialize_db:
            with PerformanceTracker("database_initialization"):
                from app.core.database import get_database
                db = await get_database()
                init_results = await initialize_database(db)
                
                logger.info(
                    "Database inizializzato",
                    indexes_created=len([k for k, v in init_results["indexes"].items() if v]),
                    admin_created=init_results["admin_created"],
                    configs_created=len([k for k, v in init_results["configs"].items() if v])
                )
        
        # Log configurazione
        logger.info(
            "✅ Applicazione inizializzata con successo",
            environment=settings.environment,
            debug=settings.debug,
            cors_origins=settings.cors_origins,
            features={
                "ai_chat": settings.ai_chat_enabled,
                "rag": settings.rag_enabled,
                "mfa": settings.mfa_enabled,
                "registration": settings.registration_enabled
            }
        )
        
        yield
        
    except Exception as e:
        logger.error("❌ Errore durante l'inizializzazione", error=str(e))
        raise
    finally:
        # Shutdown
        await log_shutdown_info()
        await disconnect_databases()
        logger.info("✅ Applicazione arrestata correttamente")


# Crea applicazione FastAPI
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,  # Disabilita docs in produzione
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# ===== MIDDLEWARE =====

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Trusted Host Middleware (sicurezza)
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )


# Middleware personalizzato per logging richieste
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware per loggare tutte le richieste HTTP"""
    import time
    import uuid
    
    # Genera ID univoco per la richiesta
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    # Log inizio richiesta
    logger.info(
        "Request started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # Processa richiesta
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log fine richiesta
        log_api_call(
            method=request.method,
            endpoint=request.url.path,
            request_id=request_id,
            duration=process_time,
            status_code=response.status_code
        )
        
        # Aggiungi headers di risposta
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        # Log errore
        log_api_call(
            method=request.method,
            endpoint=request.url.path,
            request_id=request_id,
            duration=process_time,
            status_code=500,
            error=str(e)
        )
        
        raise


# ===== EXCEPTION HANDLERS =====

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler per eccezioni HTTP"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.warning(
        "HTTP exception",
        request_id=request_id,
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler per errori di validazione"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.warning(
        "Validation error",
        request_id=request_id,
        errors=exc.errors(),
        url=str(request.url)
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Errori di validazione",
            "details": exc.errors(),
            "status_code": 422,
            "request_id": request_id
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler per eccezioni generiche"""
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    logger.error(
        "Unhandled exception",
        request_id=request_id,
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url)
    )
    
    # In produzione, non esporre dettagli dell'errore
    if settings.debug:
        error_detail = str(exc)
    else:
        error_detail = "Errore interno del server"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": error_detail,
            "status_code": 500,
            "request_id": request_id
        }
    )


# ===== ROUTE BASE =====

@app.get("/")
async def root():
    """Endpoint di benvenuto"""
    return {
        "message": f"Benvenuto nel {settings.app_name}",
        "version": settings.app_version,
        "status": "active",
        "environment": settings.environment,
        "docs": "/docs" if settings.debug else "disabled"
    }


@app.get("/health")
async def health_check():
    """Endpoint per health check"""
    try:
        # Controlla stato database
        db_health = await health_check_databases()
        
        # Determina stato generale
        all_healthy = all(db_health.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": "2024-01-20T10:30:00Z",  # datetime.utcnow().isoformat() + "Z"
            "version": settings.app_version,
            "environment": settings.environment,
            "services": {
                "api": "healthy",
                "mongodb": "healthy" if db_health.get("mongodb") else "unhealthy",
                "redis": "healthy" if db_health.get("redis") else "unhealthy"
            }
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": "2024-01-20T10:30:00Z",
                "error": str(e) if settings.debug else "Service unavailable"
            }
        )


@app.get("/info")
async def app_info():
    """Informazioni sull'applicazione"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "environment": settings.environment,
        "features": {
            "ai_chat_enabled": settings.ai_chat_enabled,
            "rag_enabled": settings.rag_enabled,
            "mfa_enabled": settings.mfa_enabled,
            "file_upload_enabled": settings.file_upload_enabled,
            "registration_enabled": settings.registration_enabled
        },
        "limits": {
            "max_file_size": settings.max_file_size,
            "allowed_extensions": settings.allowed_extensions,
            "rate_limit_per_minute": settings.rate_limit_per_minute
        }
    }


# ===== INCLUSIONE ROUTER =====

# Import e registrazione router API
from app.api.v1 import auth_routes
from app.api.v1 import users
from app.api.v1 import chat
from app.api.v1 import admin
from app.api.v1 import health

app.include_router(auth_routes.router, prefix=settings.api_prefix + "/auth", tags=["Authentication"])
app.include_router(users.router, prefix=settings.api_prefix + "/users", tags=["Users"])
app.include_router(chat.router, prefix=settings.api_prefix + "/chat", tags=["Chat"])
app.include_router(admin.router, prefix=settings.api_prefix + "/admin", tags=["Administration"])
app.include_router(health.router, prefix="/health", tags=["Health"])


# ===== AVVIO APPLICAZIONE =====

if __name__ == "__main__":
    # Configurazione per development
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
        use_colors=True
    ) 