"""
Servizio per autenticazione utenti
Gestisce login, registrazione, MFA e sessioni
"""

import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
import structlog
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.core import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    log_security_event
)
from app.models import (
    UserCreate,
    UserInDB,
    UserResponse,
    UserLogin,
    user_helper,
    PyObjectId
)


class AuthService:
    """Servizio per gestione autenticazione"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.logger = structlog.get_logger(__name__)
        
        # Statistiche
        self.stats = {
            "total_logins": 0,
            "failed_logins": 0,
            "registrations": 0,
            "mfa_setups": 0,
            "password_resets": 0
        }
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        totp_code: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[UserInDB], str]:
        """
        Autentica un utente
        
        Args:
            username: Username o email
            password: Password
            totp_code: Codice TOTP per MFA
            ip_address: IP address per audit
            
        Returns:
            Tuple (user, error_message)
        """
        try:
            # Trova utente per username o email
            user = await self.db.users.find_one({
                "$or": [
                    {"username": username.lower()},
                    {"email": username.lower()}
                ]
            })
            
            if not user:
                await self._log_auth_event(
                    None, "login_failed", "user_not_found", 
                    {"username": username}, ip_address
                )
                self.stats["failed_logins"] += 1
                return None, "Credenziali non valide"
            
            user_obj = UserInDB(**user)
            
            # Verifica se account è attivo
            if not user_obj.is_active:
                await self._log_auth_event(
                    user_obj.id, "login_failed", "account_disabled", 
                    {}, ip_address
                )
                return None, "Account disattivato"
            
            # Verifica se account è bloccato
            if user_obj.locked_until and user_obj.locked_until > datetime.utcnow():
                await self._log_auth_event(
                    user_obj.id, "login_failed", "account_locked", 
                    {"locked_until": user_obj.locked_until.isoformat()}, ip_address
                )
                return None, f"Account bloccato fino a {user_obj.locked_until}"
            
            # Verifica password
            if not verify_password(password, user_obj.password_hash):
                # Incrementa tentativi falliti
                failed_attempts = user_obj.failed_login_attempts + 1
                update_data = {"failed_login_attempts": failed_attempts}
                
                # Blocca account se troppi tentativi
                if failed_attempts >= settings.max_login_attempts:
                    lockout_time = datetime.utcnow() + timedelta(minutes=settings.lockout_duration_minutes)
                    update_data["locked_until"] = lockout_time
                
                await self.db.users.update_one(
                    {"_id": user_obj.id},
                    {"$set": update_data}
                )
                
                await self._log_auth_event(
                    user_obj.id, "login_failed", "wrong_password",
                    {"failed_attempts": failed_attempts}, ip_address
                )
                
                self.stats["failed_logins"] += 1
                return None, "Credenziali non valide"
            
            # Verifica MFA se abilitato
            if user_obj.mfa.enabled:
                if not totp_code:
                    return None, "Codice MFA richiesto"
                
                if not self._verify_totp(user_obj.mfa.secret, totp_code):
                    await self._log_auth_event(
                        user_obj.id, "login_failed", "invalid_mfa",
                        {}, ip_address
                    )
                    self.stats["failed_logins"] += 1
                    return None, "Codice MFA non valido"
                
                # Aggiorna ultimo uso MFA
                await self.db.users.update_one(
                    {"_id": user_obj.id},
                    {"$set": {"mfa.last_used": datetime.utcnow()}}
                )
            
            # Login riuscito - reset failed attempts e aggiorna last_login
            await self.db.users.update_one(
                {"_id": user_obj.id},
                {
                    "$set": {
                        "last_login": datetime.utcnow(),
                        "failed_login_attempts": 0,
                        "locked_until": None
                    },
                    "$inc": {"login_count": 1}
                }
            )
            
            await self._log_auth_event(
                user_obj.id, "login_success", "authenticated",
                {"mfa_used": user_obj.mfa.enabled}, ip_address
            )
            
            self.stats["total_logins"] += 1
            
            # Ricarica utente con dati aggiornati
            updated_user = await self.db.users.find_one({"_id": user_obj.id})
            return UserInDB(**updated_user), ""
            
        except Exception as e:
            self.logger.error("Errore autenticazione", error=str(e))
            return None, "Errore interno del server"
    
    async def create_user(
        self,
        user_data: UserCreate,
        created_by: Optional[PyObjectId] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[UserInDB], str]:
        """
        Crea un nuovo utente
        
        Args:
            user_data: Dati utente da creare
            created_by: ID utente che crea (per audit)
            ip_address: IP address per audit
            
        Returns:
            Tuple (user, error_message)
        """
        try:
            # Verifica se username esiste già
            existing_username = await self.db.users.find_one({
                "username": user_data.username.lower()
            })
            
            if existing_username:
                return None, "Username già in uso"
            
            # Verifica se email esiste già
            existing_email = await self.db.users.find_one({
                "email": user_data.email.lower()
            })
            
            if existing_email:
                return None, "Email già registrata"
            
            # Crea hash password
            password_hash = get_password_hash(user_data.password)
            
            # Prepara documento utente
            now = datetime.utcnow()
            user_doc = {
                "username": user_data.username.lower(),
                "email": user_data.email.lower(),
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "password_hash": password_hash,
                "role": user_data.role,
                "is_active": user_data.is_active,
                "is_verified": user_data.is_verified,
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
            
            if created_by:
                user_doc["created_by"] = created_by
            
            # Inserisci nel database
            result = await self.db.users.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id
            
            # Log evento
            await self._log_auth_event(
                result.inserted_id, "user_created", "registration",
                {"role": user_data.role.value, "created_by": str(created_by) if created_by else None},
                ip_address
            )
            
            self.stats["registrations"] += 1
            
            self.logger.info(
                "Utente creato",
                user_id=str(result.inserted_id),
                username=user_data.username,
                role=user_data.role.value
            )
            
            return UserInDB(**user_doc), ""
            
        except Exception as e:
            self.logger.error("Errore creazione utente", error=str(e))
            return None, "Errore interno del server"
    
    async def generate_tokens(
        self,
        user: UserInDB,
        remember_me: bool = False
    ) -> Dict[str, Any]:
        """
        Genera access e refresh token per un utente
        
        Args:
            user: Utente autenticato
            remember_me: Se True, token con durata estesa
            
        Returns:
            Dict con tokens e metadati
        """
        # Durata token
        access_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        if remember_me:
            access_expires = timedelta(days=1)
        
        refresh_expires = timedelta(days=settings.jwt_refresh_token_expire_days)
        
        # Dati payload
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "username": user.username
        }
        
        # Genera tokens
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=refresh_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_expires.total_seconds()),
            "user": UserResponse(
                **user_helper(user.model_dump()),
                id=str(user.id)
            )
        }
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Rinnova access token usando refresh token
        
        Args:
            refresh_token: Refresh token valido
            ip_address: IP address per audit
            
        Returns:
            Tuple (tokens_dict, error_message)
        """
        try:
            # Verifica refresh token
            payload = verify_token(refresh_token)
            if not payload:
                return None, "Refresh token non valido"
            
            user_id = payload.get("sub")
            if not user_id:
                return None, "Refresh token non valido"
            
            # Trova utente
            user = await self.db.users.find_one({"_id": ObjectId(user_id)})
            if not user or not user.get("is_active", False):
                return None, "Utente non trovato o disattivato"
            
            user_obj = UserInDB(**user)
            
            # Genera nuovo access token
            new_tokens = await self.generate_tokens(user_obj, remember_me=False)
            
            await self._log_auth_event(
                user_obj.id, "token_refreshed", "access_token_renewed",
                {}, ip_address
            )
            
            return new_tokens, ""
            
        except Exception as e:
            self.logger.error("Errore refresh token", error=str(e))
            return None, "Errore interno del server"
    
    async def setup_mfa(
        self,
        user_id: PyObjectId,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], str]:
        """
        Configura MFA per un utente
        
        Args:
            user_id: ID utente
            ip_address: IP address per audit
            
        Returns:
            Tuple (secret, qr_code_base64, error_message)
        """
        try:
            # Trova utente
            user = await self.db.users.find_one({"_id": user_id})
            if not user:
                return None, None, "Utente non trovato"
            
            # Genera secret TOTP
            secret = pyotp.random_base32()
            
            # Genera QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user["email"],
                issuer_name=settings.app_name
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Genera backup codes
            backup_codes = [secrets.token_hex(8) for _ in range(10)]
            
            # Salva configurazione MFA (non ancora abilitata)
            await self.db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "mfa.secret": secret,
                        "mfa.backup_codes": backup_codes,
                        "mfa.setup_completed": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            await self._log_auth_event(
                user_id, "mfa_setup_started", "totp_secret_generated",
                {}, ip_address
            )
            
            return secret, img_str, ""
            
        except Exception as e:
            self.logger.error("Errore setup MFA", error=str(e))
            return None, None, "Errore interno del server"
    
    async def enable_mfa(
        self,
        user_id: PyObjectId,
        totp_code: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, List[str], str]:
        """
        Abilita MFA dopo verifica codice TOTP
        
        Args:
            user_id: ID utente
            totp_code: Codice TOTP per verifica
            ip_address: IP address per audit
            
        Returns:
            Tuple (success, backup_codes, error_message)
        """
        try:
            # Trova utente
            user = await self.db.users.find_one({"_id": user_id})
            if not user:
                return False, [], "Utente non trovato"
            
            # Verifica che MFA sia in setup
            mfa_config = user.get("mfa", {})
            if not mfa_config.get("secret"):
                return False, [], "MFA non configurato"
            
            # Verifica codice TOTP
            if not self._verify_totp(mfa_config["secret"], totp_code):
                await self._log_auth_event(
                    user_id, "mfa_enable_failed", "invalid_totp_code",
                    {}, ip_address
                )
                return False, [], "Codice TOTP non valido"
            
            # Abilita MFA
            await self.db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "mfa.enabled": True,
                        "mfa.setup_completed": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            await self._log_auth_event(
                user_id, "mfa_enabled", "totp_activated",
                {}, ip_address
            )
            
            self.stats["mfa_setups"] += 1
            
            self.logger.info("MFA abilitato", user_id=str(user_id))
            
            return True, mfa_config.get("backup_codes", []), ""
            
        except Exception as e:
            self.logger.error("Errore abilitazione MFA", error=str(e))
            return False, [], "Errore interno del server"
    
    async def disable_mfa(
        self,
        user_id: PyObjectId,
        totp_code: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Disabilita MFA dopo verifica codice
        
        Args:
            user_id: ID utente
            totp_code: Codice TOTP per verifica
            ip_address: IP address per audit
            
        Returns:
            Tuple (success, error_message)
        """
        try:
            # Trova utente
            user = await self.db.users.find_one({"_id": user_id})
            if not user:
                return False, "Utente non trovato"
            
            # Verifica che MFA sia abilitato
            mfa_config = user.get("mfa", {})
            if not mfa_config.get("enabled"):
                return False, "MFA non abilitato"
            
            # Verifica codice TOTP
            if not self._verify_totp(mfa_config["secret"], totp_code):
                await self._log_auth_event(
                    user_id, "mfa_disable_failed", "invalid_totp_code",
                    {}, ip_address
                )
                return False, "Codice TOTP non valido"
            
            # Disabilita MFA
            await self.db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "mfa.enabled": False,
                        "mfa.secret": None,
                        "mfa.backup_codes": [],
                        "mfa.setup_completed": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            await self._log_auth_event(
                user_id, "mfa_disabled", "totp_deactivated",
                {}, ip_address
            )
            
            self.logger.info("MFA disabilitato", user_id=str(user_id))
            
            return True, ""
            
        except Exception as e:
            self.logger.error("Errore disabilitazione MFA", error=str(e))
            return False, "Errore interno del server"
    
    def _verify_totp(self, secret: str, token: str) -> bool:
        """Verifica codice TOTP"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Finestra di 30 secondi
        except Exception as e:
            self.logger.error("Errore verifica TOTP", error=str(e))
            return False
    
    async def _log_auth_event(
        self,
        user_id: Optional[PyObjectId],
        action: str,
        result: str,
        details: Dict[str, Any],
        ip_address: Optional[str]
    ):
        """Log eventi di autenticazione"""
        await log_security_event(
            user_id=str(user_id) if user_id else None,
            action=action,
            details={**details, "result": result},
            ip_address=ip_address,
            severity="info" if result in ["authenticated", "user_created"] else "warning"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Ritorna statistiche del servizio"""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset statistiche"""
        self.stats = {
            "total_logins": 0,
            "failed_logins": 0,
            "registrations": 0,
            "mfa_setups": 0,
            "password_resets": 0
        }
        self.logger.info("Statistiche Auth Service resettate") 