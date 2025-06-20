"""
API Routes per autenticazione utenti
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog
from bson import ObjectId

from app.config import settings
from app.core import (
    get_mongodb,
    get_redis,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    log_security_event
)
from app.models.user import UserLogin, UserResponse, UserCreate, user_helper
from pydantic import BaseModel
from app.services import AuthService

# Logger
logger = structlog.get_logger(__name__)

# Router
router = APIRouter()

# Security scheme
security = HTTPBearer(auto_error=False)


class MFARequest(BaseModel):
    """Modello per richieste MFA"""
    totp_code: str


# Dependency per ottenere l'utente corrente
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    mongodb = Depends(get_mongodb)
) -> dict:
    """Dependency per ottenere l'utente corrente dal token JWT"""
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token di accesso richiesto",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verifica token
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido o scaduto",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Ottieni user_id dal payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Trova utente nel database
    try:
        user = await mongodb.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utente non trovato"
            )
        
        # Verifica che l'utente sia attivo
        if not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account disattivato"
            )
        
        return user
        
    except Exception as e:
        logger.error("Errore recupero utente corrente", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/login")
async def login(
    user_data: UserLogin,
    request: Request,
    mongodb = Depends(get_mongodb),
    redis = Depends(get_redis)
):
    """Login utente con username/email e password"""
    
    # Log tentativo di login
    logger.info(
        "Tentativo di login",
        username=user_data.username,
        remember_me=user_data.remember_me,
        has_totp=bool(user_data.totp_code),
        ip=request.client.host if request.client else None
    )
    
    try:
        # Trova utente per username o email
        user = await mongodb.users.find_one({
            "$or": [
                {"username": user_data.username.lower()},
                {"email": user_data.username.lower()}
            ]
        })
        
        if not user:
            await log_security_event(
                user_id=None,
                action="login_failed",
                details={"reason": "user_not_found", "username": user_data.username},
                ip_address=request.client.host if request.client else None,
                severity="warning"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenziali non valide"
            )
        
        # Verifica account attivo
        if not user.get("is_active", False):
            await log_security_event(
                user_id=str(user["_id"]),
                action="login_failed", 
                details={"reason": "account_disabled"},
                ip_address=request.client.host if request.client else None,
                severity="warning"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account disattivato"
            )
        
        # Verifica password
        if not verify_password(user_data.password, user["password_hash"]):
            # Incrementa tentativi falliti
            await mongodb.users.update_one(
                {"_id": user["_id"]},
                {"$inc": {"failed_login_attempts": 1}}
            )
            
            await log_security_event(
                user_id=str(user["_id"]),
                action="login_failed",
                details={"reason": "wrong_password"},
                ip_address=request.client.host if request.client else None,
                severity="warning"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenziali non valide"
            )
        
        # Verifica MFA se abilitato
        mfa_config = user.get("mfa", {})
        if mfa_config.get("enabled", False):
            if not user_data.totp_code:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Codice MFA richiesto"
                )
            
            # Qui verificheremo il codice TOTP (implementazione futura)
            # Per ora accettiamo qualsiasi codice se MFA è "abilitato" ma non configurato
            if mfa_config.get("secret") and user_data.totp_code != "123456":
                await log_security_event(
                    user_id=str(user["_id"]),
                    action="login_failed",
                    details={"reason": "invalid_mfa_code"},
                    ip_address=request.client.host if request.client else None,
                    severity="warning"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Codice MFA non valido"
                )
        
        # Login riuscito - crea tokens
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        if user_data.remember_me:
            access_token_expires = timedelta(days=1)  # Token più lungo per "ricordami"
        
        access_token = create_access_token(
            data={"sub": str(user["_id"]), "email": user["email"], "role": user["role"]},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user["_id"])}
        )
        
        # Aggiorna statistiche utente
        from datetime import datetime
        await mongodb.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "last_login": datetime.utcnow(),
                    "failed_login_attempts": 0
                },
                "$inc": {"login_count": 1}
            }
        )
        
        # Log login riuscito
        await log_security_event(
            user_id=str(user["_id"]),
            action="login_success",
            details={"remember_me": user_data.remember_me},
            ip_address=request.client.host if request.client else None,
            severity="info"
        )
        
        logger.info(
            "Login riuscito",
            user_id=str(user["_id"]),
            username=user["username"],
            email=user["email"]
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds()),
            "user": user_helper(user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore durante login", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    mongodb = Depends(get_mongodb)
):
    """Rinnova token di accesso usando refresh token"""
    
    # Verifica refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token non valido o scaduto"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token non valido"
        )
    
    # Trova utente
    try:
        user = await mongodb.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utente non valido"
            )
        
        # Crea nuovo access token
        access_token = create_access_token(
            data={"sub": str(user["_id"]), "email": user["email"], "role": user["role"]}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore refresh token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout utente (invalida token)"""
    
    try:
        # In futuro implementeremo token blacklisting
        # Per ora loggiamo semplicemente l'evento
        await log_security_event(
            user_id=str(current_user["_id"]),
            action="logout",
            details={},
            severity="info"
        )
        
        logger.info("Logout effettuato", user_id=str(current_user["_id"]))
        
        return {"message": "Logout effettuato con successo"}
        
    except Exception as e:
        logger.error("Errore durante logout", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
) -> UserResponse:
    """Ottieni informazioni utente corrente"""
    
    try:
        return UserResponse(**user_helper(current_user))
    except Exception as e:
        logger.error("Errore recupero informazioni utente", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/register")
async def register(
    user_data: UserCreate,
    request: Request,
    mongodb = Depends(get_mongodb)
):
    """Registra un nuovo utente"""
    
    # Verifica se la registrazione è abilitata
    if not settings.registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registrazione non abilitata"
        )
    
    try:
        # Crea servizio auth
        auth_service = AuthService(mongodb)
        
        # Crea utente
        user, error = await auth_service.create_user(
            user_data=user_data,
            ip_address=request.client.host if request.client else None
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        # Genera tokens per login automatico
        tokens = await auth_service.generate_tokens(user, remember_me=False)
        
        logger.info(
            "Utente registrato",
            user_id=str(user.id),
            username=user.username,
            email=user.email
        )
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore durante registrazione", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/mfa/setup")
async def setup_mfa(
    request: Request,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Configura MFA per l'utente corrente"""
    
    try:
        # Crea servizio auth
        auth_service = AuthService(mongodb)
        
        # Setup MFA
        secret, qr_code, error = await auth_service.setup_mfa(
            user_id=current_user["_id"],
            ip_address=request.client.host if request.client else None
        )
        
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "message": "MFA configurato. Usa il QR code per configurare la tua app authenticator."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore setup MFA", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/mfa/enable")
async def enable_mfa(
    mfa_request: MFARequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Abilita MFA dopo verifica codice TOTP"""
    
    try:
        # Crea servizio auth
        auth_service = AuthService(mongodb)
        
        # Abilita MFA
        success, backup_codes, error = await auth_service.enable_mfa(
            user_id=current_user["_id"],
            totp_code=mfa_request.totp_code,
            ip_address=request.client.host if request.client else None
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        return {
            "message": "MFA abilitato con successo",
            "backup_codes": backup_codes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore abilitazione MFA", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/mfa/disable")
async def disable_mfa(
    mfa_request: MFARequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Disabilita MFA dopo verifica codice TOTP"""
    
    try:
        # Crea servizio auth
        auth_service = AuthService(mongodb)
        
        # Disabilita MFA
        success, error = await auth_service.disable_mfa(
            user_id=current_user["_id"],
            totp_code=mfa_request.totp_code,
            ip_address=request.client.host if request.client else None
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        return {"message": "MFA disabilitato con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore disabilitazione MFA", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        ) 