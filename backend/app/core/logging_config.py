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