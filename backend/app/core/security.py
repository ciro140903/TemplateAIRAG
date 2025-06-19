"""
Sistema di sicurezza per autenticazione e autorizzazione
Gestisce JWT tokens, password hashing, e verifica accessi
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog
from bson import ObjectId

from app.config import settings
from app.core.database import redis_manager

# Logger strutturato
logger = structlog.get_logger(__name__)

# Configurazione password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Manager centralizzato per le operazioni di sicurezza"""
    
    def __init__(self):
        self.algorithm = settings.jwt_algorithm
        self.secret_key = settings.jwt_secret
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
    
    # ===== PASSWORD HASHING =====
    
    def hash_password(self, password: str) -> str:
        """Genera hash sicuro della password"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica che la password corrisponda all'hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_password_reset_token(self, email: str) -> str:
        """Genera token sicuro per reset password"""
        # Token che scade in 1 ora
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode = {
            "sub": email,
            "exp": expire,
            "type": "password_reset",
            "iat": datetime.utcnow()
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verifica token di reset password e ritorna email"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email = payload.get("sub")
            token_type = payload.get("type")
            
            if email is None or token_type != "password_reset":
                return None
            
            return email
        except JWTError:
            return None
    
    # ===== JWT TOKENS =====
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Crea token JWT di accesso"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # Aggiungi claims standard
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": self._generate_jti()  # JWT ID per blacklist
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info("Access token creato", user_id=data.get("sub"), expires=expire)
        
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Crea token JWT di refresh"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": self._generate_jti()
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info("Refresh token creato", user_id=data.get("sub"), expires=expire)
        
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verifica token JWT e ritorna payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verifica tipo token
            if payload.get("type") != token_type:
                logger.warning("Tipo token non valido", expected=token_type, actual=payload.get("type"))
                return None
            
            # Verifica se token è in blacklist
            jti = payload.get("jti")
            if jti and self._is_token_blacklisted(jti):
                logger.warning("Token in blacklist", jti=jti)
                return None
            
            return payload
            
        except JWTError as e:
            logger.warning("Errore verifica token", error=str(e))
            return None
    
    async def blacklist_token(self, token: str) -> bool:
        """Aggiunge token alla blacklist"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # Non verifichiamo scadenza per blacklist
            )
            
            jti = payload.get("jti")
            if not jti:
                return False
            
            # Calcola tempo di scadenza per la blacklist
            exp = payload.get("exp")
            if exp:
                expire_time = exp - int(datetime.utcnow().timestamp())
                if expire_time > 0:
                    await redis_manager.blacklist_token(jti, expire_time)
                    logger.info("Token aggiunto alla blacklist", jti=jti)
                    return True
            
            return False
            
        except JWTError:
            return False
    
    def _generate_jti(self) -> str:
        """Genera JWT ID univoco"""
        return secrets.token_urlsafe(32)
    
    def _is_token_blacklisted(self, jti: str) -> bool:
        """Controlla se token è in blacklist (versione sincrona)"""
        # Per ora ritorna False, implementeremo versione async nelle API
        return False
    
    # ===== UTILITY FUNCTIONS =====
    
    def generate_api_key(self, length: int = 32) -> str:
        """Genera API key sicura"""
        return secrets.token_urlsafe(length)
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Genera token sicuro generico"""
        return secrets.token_urlsafe(length)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash di API key per storage sicuro"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verifica API key contro hash"""
        return hashlib.sha256(api_key.encode()).hexdigest() == hashed_key


class AuthenticationError(Exception):
    """Eccezione per errori di autenticazione"""
    pass


class AuthorizationError(Exception):
    """Eccezione per errori di autorizzazione"""
    pass


# Istanza globale del security manager
security_manager = SecurityManager()


# ===== FUNZIONI DI UTILITÀ =====

def get_password_hash(password: str) -> str:
    """Genera hash della password"""
    return security_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica password"""
    return security_manager.verify_password(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea access token"""
    return security_manager.create_access_token(data, expires_delta)


def create_refresh_token(data: dict) -> str:
    """Crea refresh token"""
    return security_manager.create_refresh_token(data)


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verifica token"""
    return security_manager.verify_token(token, token_type)


# ===== DECORATORI PER AUTORIZZAZIONE =====

def require_roles(*roles):
    """Decoratore per richiedere ruoli specifici"""
    def decorator(func):
        func._required_roles = roles
        return func
    return decorator


def require_permissions(*permissions):
    """Decoratore per richiedere permessi specifici"""
    def decorator(func):
        func._required_permissions = permissions
        return func
    return decorator


# ===== FUNZIONI PER MFA =====

def generate_mfa_secret() -> str:
    """Genera secret per TOTP MFA"""
    import pyotp
    return pyotp.random_base32()


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """Verifica codice TOTP"""
    try:
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    except Exception as e:
        logger.error("Errore verifica TOTP", error=str(e))
        return False


def generate_backup_codes(count: int = 10) -> list:
    """Genera codici di backup per MFA"""
    return [secrets.token_hex(4).upper() for _ in range(count)]


def get_totp_uri(secret: str, email: str, issuer: str = None) -> str:
    """Genera URI per QR code TOTP"""
    try:
        import pyotp
        if not issuer:
            issuer = settings.app_name
        
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=issuer
        )
    except Exception as e:
        logger.error("Errore generazione TOTP URI", error=str(e))
        return ""


# ===== FUNZIONI PER RATE LIMITING =====

async def check_rate_limit(
    identifier: str, 
    limit: int = None, 
    window: int = 60
) -> tuple[bool, int]:
    """
    Controlla rate limiting per identificatore (IP, user_id, etc.)
    Ritorna (allowed, remaining_requests)
    """
    if limit is None:
        limit = settings.rate_limit_per_minute
    
    key = f"rate_limit:{identifier}"
    
    try:
        current_count = await redis_manager.get_cache(key)
        
        if current_count is None:
            # Prima richiesta nella finestra
            await redis_manager.set_cache(key, "1", window)
            return True, limit - 1
        
        current_count = int(current_count)
        
        if current_count >= limit:
            return False, 0
        
        # Incrementa contatore
        new_count = current_count + 1
        await redis_manager.set_cache(key, str(new_count), window)
        
        return True, limit - new_count
        
    except Exception as e:
        logger.error("Errore controllo rate limit", error=str(e))
        # In caso di errore, permettiamo la richiesta
        return True, limit


# ===== FUNZIONI PER AUDIT LOGGING =====

async def log_security_event(
    user_id: Optional[str],
    action: str,
    details: Dict[str, Any],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    severity: str = "info"
) -> None:
    """Registra evento di sicurezza nei log di audit"""
    from app.core.database import mongodb_manager
    
    try:
        audit_entry = {
            "user_id": ObjectId(user_id) if user_id else None,
            "action": action,
            "resource_type": "security",
            "resource_id": None,
            "details": details,
            "timestamp": datetime.utcnow(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "severity": severity
        }
        
        await mongodb_manager.audit_logs.insert_one(audit_entry)
        
        # Log anche con structlog
        logger.info(
            "Security event",
            user_id=user_id,
            action=action,
            severity=severity,
            **details
        )
        
    except Exception as e:
        logger.error("Errore logging security event", error=str(e))


# ===== FUNZIONI PER VALIDAZIONE INPUT =====

def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitizza input utente"""
    if not input_str:
        return ""
    
    # Tronca se troppo lungo
    sanitized = input_str[:max_length]
    
    # Rimuovi caratteri potenzialmente pericolosi
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()


def validate_object_id(obj_id: str) -> bool:
    """Valida formato ObjectId MongoDB"""
    try:
        ObjectId(obj_id)
        return True
    except:
        return False


# ===== CONFIGURAZIONE CORS SICURA =====

def get_cors_origins() -> list:
    """Ritorna origini CORS configurate in modo sicuro"""
    if settings.environment == "development":
        return settings.cors_origins
    else:
        # In produzione, usa solo origini specifiche
        return [origin for origin in settings.cors_origins if not origin.startswith("http://localhost")] 