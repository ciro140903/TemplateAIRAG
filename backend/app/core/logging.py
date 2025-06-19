"""
Sistema di logging strutturato per il Portale Aziendale
Invia log a Loki e gestisce logging locale con structlog
"""

import sys
import json
import logging
import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger

from app.config import settings


class LokiHandler(logging.Handler):
    """Handler personalizzato per inviare log a Loki"""
    
    def __init__(self, loki_url: str = None):
        super().__init__()
        self.loki_url = loki_url or settings.loki_url
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Configura sessione HTTP per Loki"""
        try:
            import httpx
            self.session = httpx.AsyncClient(
                timeout=5.0,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        except ImportError:
            # Se httpx non è disponibile, usa requests
            import requests
            self.session = requests.Session()
    
    def emit(self, record):
        """Invia log record a Loki"""
        try:
            # Crea payload per Loki
            log_entry = self.format(record)
            timestamp = str(int(record.created * 1000000000))  # Nanoseconds
            
            # Labels per Loki
            labels = {
                "job": "portal_backend",
                "level": record.levelname.lower(),
                "service": "api",
                "environment": settings.environment
            }
            
            # Aggiungi labels aggiuntivi dal record
            if hasattr(record, 'user_id'):
                labels["user_id"] = str(record.user_id)
            if hasattr(record, 'action'):
                labels["action"] = record.action
            if hasattr(record, 'module'):
                labels["module"] = record.module
            
            # Costruisci payload Loki
            payload = {
                "streams": [
                    {
                        "stream": labels,
                        "values": [[timestamp, log_entry]]
                    }
                ]
            }
            
            # Invia a Loki (in modo asincrono se possibile)
            self._send_to_loki(payload)
            
        except Exception as e:
            # Non bloccare l'applicazione per errori di logging
            print(f"Errore invio log a Loki: {e}", file=sys.stderr)
    
    def _send_to_loki(self, payload):
        """Invia payload a Loki"""
        try:
            if hasattr(self.session, 'post'):
                # Richiesta sincrona
                response = self.session.post(
                    f"{self.loki_url}/loki/api/v1/push",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                response.raise_for_status()
        except Exception:
            # Ignora errori di rete per non bloccare l'app
            pass


class ContextFilter(logging.Filter):
    """Filtro per aggiungere contesto alle log entries"""
    
    def filter(self, record):
        # Aggiungi timestamp in formato ISO
        record.timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Aggiungi informazioni applicazione
        record.app_name = settings.app_name
        record.app_version = settings.app_version
        record.environment = settings.environment
        
        return True


def setup_logging():
    """Configura il sistema di logging strutturato"""
    
    # Configurazione structlog
    structlog.configure(
        processors=[
            # Aggiungi timestamp
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Processore JSON per output strutturato
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurazione logger Python standard
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Rimuovi handler esistenti
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler per console (JSON format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(ContextFilter())
    root_logger.addHandler(console_handler)
    
    # Handler per Loki (se configurato)
    if settings.loki_url and not settings.debug:
        try:
            loki_handler = LokiHandler(settings.loki_url)
            loki_formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(name)s %(levelname)s %(message)s'
            )
            loki_handler.setFormatter(loki_formatter)
            loki_handler.addFilter(ContextFilter())
            root_logger.addHandler(loki_handler)
        except Exception as e:
            print(f"Impossibile configurare Loki handler: {e}", file=sys.stderr)
    
    # Configurazione livelli per librerie esterne
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log inizializzazione
    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging system initialized",
        log_level=settings.log_level,
        loki_enabled=bool(settings.loki_url and not settings.debug),
        environment=settings.environment
    )


# Decoratore per logging automatico delle funzioni
def log_function_call(include_args: bool = False, include_result: bool = False):
    """Decoratore per loggare automaticamente le chiamate alle funzioni"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger = structlog.get_logger(func.__module__)
            
            log_data = {
                "function": func.__name__,
                "action": "function_call"
            }
            
            if include_args:
                # Sanitizza gli argomenti per evitare di loggare password/token
                safe_args = []
                for arg in args:
                    if isinstance(arg, str) and len(arg) > 50:
                        safe_args.append(f"{arg[:50]}...")
                    else:
                        safe_args.append(str(arg))
                
                safe_kwargs = {}
                for k, v in kwargs.items():
                    if any(sensitive in k.lower() for sensitive in ['password', 'token', 'secret', 'key']):
                        safe_kwargs[k] = "[HIDDEN]"
                    elif isinstance(v, str) and len(v) > 50:
                        safe_kwargs[k] = f"{v[:50]}..."
                    else:
                        safe_kwargs[k] = v
                
                log_data["args"] = safe_args
                log_data["kwargs"] = safe_kwargs
            
            start_time = datetime.utcnow()
            logger.info("Function started", **log_data)
            
            try:
                result = await func(*args, **kwargs)
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                log_data["duration_seconds"] = duration
                log_data["status"] = "success"
                
                if include_result and result is not None:
                    # Sanitizza il risultato
                    if isinstance(result, dict):
                        safe_result = {k: "[HIDDEN]" if any(s in k.lower() for s in ['password', 'token']) else v 
                                     for k, v in result.items()}
                        log_data["result"] = safe_result
                    elif hasattr(result, '__dict__'):
                        log_data["result_type"] = type(result).__name__
                    else:
                        log_data["result"] = str(result)[:100]
                
                logger.info("Function completed", **log_data)
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                log_data["duration_seconds"] = duration
                log_data["status"] = "error"
                log_data["error"] = str(e)
                log_data["error_type"] = type(e).__name__
                
                logger.error("Function failed", **log_data)
                raise
        
        def sync_wrapper(*args, **kwargs):
            # Versione sincrona del wrapper
            logger = structlog.get_logger(func.__module__)
            
            log_data = {"function": func.__name__, "action": "function_call"}
            
            start_time = datetime.utcnow()
            logger.info("Function started", **log_data)
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                log_data["duration_seconds"] = duration
                log_data["status"] = "success"
                
                logger.info("Function completed", **log_data)
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                log_data["duration_seconds"] = duration
                log_data["status"] = "error"
                log_data["error"] = str(e)
                
                logger.error("Function failed", **log_data)
                raise
        
        # Ritorna wrapper appropriato basato sul tipo di funzione
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Funzioni di utility per logging strutturato
def get_request_logger(request_id: str = None, user_id: str = None):
    """Crea logger con contesto di richiesta"""
    logger = structlog.get_logger()
    
    context = {}
    if request_id:
        context["request_id"] = request_id
    if user_id:
        context["user_id"] = user_id
    
    return logger.bind(**context)


def log_api_call(
    method: str,
    endpoint: str,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    duration: Optional[float] = None,
    status_code: Optional[int] = None,
    error: Optional[str] = None
):
    """Log standardizzato per chiamate API"""
    logger = structlog.get_logger("api")
    
    log_data = {
        "action": "api_call",
        "method": method,
        "endpoint": endpoint,
        "user_id": user_id,
        "request_id": request_id,
        "duration_seconds": duration,
        "status_code": status_code
    }
    
    if error:
        log_data["error"] = error
        logger.error("API call failed", **log_data)
    else:
        logger.info("API call completed", **log_data)


def log_database_operation(
    operation: str,
    collection: str,
    user_id: Optional[str] = None,
    document_id: Optional[str] = None,
    duration: Optional[float] = None,
    error: Optional[str] = None
):
    """Log standardizzato per operazioni database"""
    logger = structlog.get_logger("database")
    
    log_data = {
        "action": "database_operation",
        "operation": operation,
        "collection": collection,
        "user_id": user_id,
        "document_id": document_id,
        "duration_seconds": duration
    }
    
    if error:
        log_data["error"] = error
        logger.error("Database operation failed", **log_data)
    else:
        logger.info("Database operation completed", **log_data)


def log_ai_interaction(
    interaction_type: str,
    model: str,
    user_id: Optional[str] = None,
    tokens_used: Optional[int] = None,
    duration: Optional[float] = None,
    error: Optional[str] = None
):
    """Log standardizzato per interazioni AI"""
    logger = structlog.get_logger("ai")
    
    log_data = {
        "action": "ai_interaction",
        "interaction_type": interaction_type,
        "model": model,
        "user_id": user_id,
        "tokens_used": tokens_used,
        "duration_seconds": duration
    }
    
    if error:
        log_data["error"] = error
        logger.error("AI interaction failed", **log_data)
    else:
        logger.info("AI interaction completed", **log_data)


# Middleware per logging richieste HTTP
class LoggingMiddleware:
    """Middleware per loggare automaticamente tutte le richieste HTTP"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Genera ID univoco per la richiesta
            import uuid
            request_id = str(uuid.uuid4())
            
            # Aggiungi request_id al scope
            scope["request_id"] = request_id
            
            start_time = datetime.utcnow()
            
            # Log inizio richiesta
            logger = structlog.get_logger("middleware")
            logger.info(
                "Request started",
                request_id=request_id,
                method=scope["method"],
                path=scope["path"],
                query_string=scope.get("query_string", b"").decode(),
                client=scope.get("client")
            )
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    # Log fine richiesta
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    logger.info(
                        "Request completed",
                        request_id=request_id,
                        status_code=message["status"],
                        duration_seconds=duration
                    )
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


# Configurazione metriche per monitoring
def setup_metrics():
    """Configura metriche Prometheus per monitoring"""
    if not settings.enable_metrics:
        return None
    
    try:
        from prometheus_client import Counter, Histogram, Gauge, start_http_server
        
        # Metriche API
        api_requests_total = Counter(
            'portal_api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status_code']
        )
        
        api_request_duration = Histogram(
            'portal_api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint']
        )
        
        # Metriche database
        db_operations_total = Counter(
            'portal_db_operations_total',
            'Total database operations',
            ['operation', 'collection', 'status']
        )
        
        db_operation_duration = Histogram(
            'portal_db_operation_duration_seconds',
            'Database operation duration',
            ['operation', 'collection']
        )
        
        # Metriche AI
        ai_requests_total = Counter(
            'portal_ai_requests_total',
            'Total AI requests',
            ['model', 'type', 'status']
        )
        
        ai_tokens_used = Counter(
            'portal_ai_tokens_used_total',
            'Total AI tokens used',
            ['model', 'type']
        )
        
        # Metriche sistema
        active_users = Gauge(
            'portal_active_users',
            'Number of active users'
        )
        
        # Avvia server metriche
        start_http_server(settings.metrics_port)
        
        logger = structlog.get_logger(__name__)
        logger.info(
            "Metrics server started",
            port=settings.metrics_port,
            endpoint=f"http://localhost:{settings.metrics_port}/metrics"
        )
        
        return {
            'api_requests_total': api_requests_total,
            'api_request_duration': api_request_duration,
            'db_operations_total': db_operations_total,
            'db_operation_duration': db_operation_duration,
            'ai_requests_total': ai_requests_total,
            'ai_tokens_used': ai_tokens_used,
            'active_users': active_users
        }
        
    except ImportError as e:
        logger = structlog.get_logger(__name__)
        logger.warning("Prometheus client not available, metrics disabled", error=str(e))
        return None 