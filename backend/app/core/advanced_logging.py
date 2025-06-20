"""
Sistema di logging avanzato con structured logging
Implementa logging strutturato per API, sicurezza, performance e debug
"""

import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
import logging
import logging.handlers
from pythonjsonlogger import jsonlogger

from app.config import settings


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Formatter JSON personalizzato per log strutturati"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Aggiungi timestamp in formato ISO
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Aggiungi livello log
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        
        # Aggiungi informazioni applicazione
        log_record['service'] = settings.app_name
        log_record['version'] = settings.app_version
        log_record['environment'] = settings.environment


class PerformanceFilter(logging.Filter):
    """Filtro per log di performance - registra solo operazioni lente"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Filtra solo log con duration > soglia
        if hasattr(record, 'duration') and isinstance(record.duration, (int, float)):
            return record.duration > 1.0  # Solo operazioni > 1 secondo
        return True


class SecurityFilter(logging.Filter):
    """Filtro per log di sicurezza - evidenzia eventi critici"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Aggiungi flag per eventi di sicurezza
        security_actions = [
            'login_failed', 'login_success', 'logout',
            'password_changed', 'mfa_enabled', 'mfa_disabled',
            'user_created', 'user_deleted', 'role_changed',
            'suspicious_activity', 'rate_limit_exceeded'
        ]
        
        if hasattr(record, 'action') and record.action in security_actions:
            record.security_event = True
            
            # Eleva livello per eventi critici
            critical_actions = ['login_failed', 'suspicious_activity', 'rate_limit_exceeded']
            if record.action in critical_actions:
                record.levelno = logging.WARNING
                record.levelname = 'WARNING'
        
        return True


def setup_structured_logging() -> None:
    """
    Configura sistema di logging strutturato
    """
    
    # Crea directory logs se non esistente
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # ===== CONFIGURAZIONE STRUTTURATA =====
    
    # Configura processori structlog
    processors = [
        # Aggiungi timestamp
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        
        # Aggiungi context variables
        structlog.contextvars.merge_contextvars,
        
        # Filtra campi sensibili
        structlog.processors.filter_by_level,
        
        # Aggiungi stack info per errori
        structlog.dev.set_exc_info,
        
        # Formato finale
        structlog.processors.JSONRenderer() if not settings.debug else structlog.dev.ConsoleRenderer()
    ]
    
    # Configura structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # ===== CONFIGURAZIONE LOGGER STANDARD =====
    
    # Logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Rimuovi handler esistenti
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # ===== HANDLER FILE =====
    
    # Handler generale
    general_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    general_handler.setLevel(logging.INFO)
    general_handler.setFormatter(CustomJSONFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s'
    ))
    
    # Handler errori
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "errors.log",
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(CustomJSONFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s %(exc_info)s'
    ))
    
    # Handler sicurezza
    security_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "security.log",
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=20,  # Mantieni più backup per sicurezza
        encoding='utf-8'
    )
    security_handler.setLevel(logging.INFO)
    security_handler.addFilter(SecurityFilter())
    security_handler.setFormatter(CustomJSONFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s'
    ))
    
    # Handler performance
    performance_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "performance.log",
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=5,
        encoding='utf-8'
    )
    performance_handler.setLevel(logging.INFO)
    performance_handler.addFilter(PerformanceFilter())
    performance_handler.setFormatter(CustomJSONFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s'
    ))
    
    # ===== HANDLER CONSOLE =====
    
    if settings.debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        if settings.log_format == "json":
            console_handler.setFormatter(CustomJSONFormatter())
        else:
            console_handler.setFormatter(logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
        
        root_logger.addHandler(console_handler)
    
    # Aggiungi tutti gli handler
    root_logger.addHandler(general_handler)
    root_logger.addHandler(error_handler)
    
    # Logger specifici
    security_logger = logging.getLogger("security")
    security_logger.addHandler(security_handler)
    security_logger.propagate = False
    
    performance_logger = logging.getLogger("performance")
    performance_logger.addHandler(performance_handler)
    performance_logger.propagate = False
    
    # ===== CONFIGURAZIONE LOGGER TERZE PARTI =====
    
    # Riduci verbosità logger esterni
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)


class LogContext:
    """Context manager per logging con contesto"""
    
    def __init__(self, **context):
        self.context = context
    
    def __enter__(self):
        bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        clear_contextvars()


class PerformanceTracker:
    """Tracker per misurare performance delle operazioni"""
    
    def __init__(self, operation_name: str, logger: Optional[structlog.BoundLogger] = None):
        self.operation_name = operation_name
        self.logger = logger or structlog.get_logger("performance")
        self.start_time = None
        self.context = {}
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            
            log_data = {
                "operation": self.operation_name,
                "duration": round(duration, 4),
                "success": exc_type is None,
                **self.context
            }
            
            if exc_type:
                log_data["error"] = str(exc_val)
                self.logger.error("Operation failed", **log_data)
            else:
                if duration > 1.0:
                    self.logger.warning("Slow operation", **log_data)
                else:
                    self.logger.info("Operation completed", **log_data)
    
    def add_context(self, **context):
        """Aggiungi contesto alla misurazione"""
        self.context.update(context)


async def log_api_call(
    method: str,
    endpoint: str,
    request_id: str,
    duration: float,
    status_code: int,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """
    Log chiamata API con structured logging
    """
    logger = structlog.get_logger("api")
    
    log_data = {
        "request_id": request_id,
        "method": method,
        "endpoint": endpoint,
        "duration": round(duration, 4),
        "status_code": status_code,
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if ip_address:
        log_data["ip_address"] = ip_address
    if user_agent:
        log_data["user_agent"] = user_agent
    if error:
        log_data["error"] = error
    
    # Determina livello log
    if status_code >= 500:
        logger.error("API call failed", **log_data)
    elif status_code >= 400:
        logger.warning("API call error", **log_data)
    elif duration > 2.0:
        logger.warning("Slow API call", **log_data)
    else:
        logger.info("API call", **log_data)


async def log_security_event(
    user_id: Optional[str],
    action: str,
    details: Dict[str, Any],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    severity: str = "info",
    session_id: Optional[str] = None
) -> None:
    """
    Log evento di sicurezza
    """
    logger = structlog.get_logger("security")
    
    log_data = {
        "action": action,
        "severity": severity,
        "details": details,
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if ip_address:
        log_data["ip_address"] = ip_address
    if user_agent:
        log_data["user_agent"] = user_agent
    if session_id:
        log_data["session_id"] = session_id
    
    # Log basato su severità
    if severity == "critical":
        logger.critical("Security event", **log_data)
    elif severity == "warning":
        logger.warning("Security event", **log_data)
    elif severity == "error":
        logger.error("Security event", **log_data)
    else:
        logger.info("Security event", **log_data)


class DatabaseQueryLogger:
    """Logger per query database con performance tracking"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.logger = structlog.get_logger("database")
    
    async def log_query(
        self,
        operation: str,
        query: Dict[str, Any],
        duration: float,
        result_count: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """Log query database"""
        
        log_data = {
            "collection": self.collection_name,
            "operation": operation,
            "duration": round(duration, 4),
        }
        
        # Non loggare query complete per privacy/performance
        if len(str(query)) < 500:
            log_data["query"] = query
        else:
            log_data["query_size"] = len(str(query))
        
        if result_count is not None:
            log_data["result_count"] = result_count
        
        if error:
            log_data["error"] = error
            self.logger.error("Database query failed", **log_data)
        elif duration > 0.5:  # Query lente > 500ms
            self.logger.warning("Slow database query", **log_data)
        else:
            self.logger.debug("Database query", **log_data)


def get_request_logger(request_id: str) -> structlog.BoundLogger:
    """
    Ottieni logger con request ID bound
    """
    return structlog.get_logger().bind(request_id=request_id)


def get_user_logger(user_id: str) -> structlog.BoundLogger:
    """
    Ottieni logger con user ID bound
    """
    return structlog.get_logger().bind(user_id=user_id)


async def log_startup_info() -> None:
    """Log informazioni di startup"""
    logger = structlog.get_logger("startup")
    
    logger.info(
        "Application starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        debug=settings.debug,
        api_host=settings.api_host,
        api_port=settings.api_port
    )


async def log_shutdown_info() -> None:
    """Log informazioni di shutdown"""
    logger = structlog.get_logger("shutdown")
    
    logger.info(
        "Application shutting down",
        app_name=settings.app_name,
        version=settings.app_version
    ) 