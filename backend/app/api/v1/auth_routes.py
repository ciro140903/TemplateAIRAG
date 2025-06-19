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
    verify_token
)
from app.models.user import UserLogin, UserResponse, user_helper

# Logger
logger = structlog.get_logger(__name__)

# Router
router = APIRouter()

# Security scheme
security = HTTPBearer(auto_error=False)


@router.post("/login")
async def login(
    user_data: UserLogin,
    request: Request,
    mongodb = Depends(get_mongodb)
):
    """Login utente con username/email e password"""
    
    logger.info("Tentativo di login", username=user_data.username)
    
    try:
        # Trova utente per username o email
        user = await mongodb.users.find_one({
            "$or": [
                {"username": user_data.username.lower()},
                {"email": user_data.username.lower()}
            ]
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenziali non valide"
            )
        
        # Verifica account attivo
        if not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account disattivato"
            )
        
        # Verifica password
        if not verify_password(user_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenziali non valide"
            )
        
        # Crea tokens
        access_token = create_access_token(
            data={"sub": str(user["_id"]), "email": user["email"], "role": user["role"]}
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user["_id"])}
        )
        
        logger.info("Login riuscito", user_id=str(user["_id"]))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
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


@router.get("/test")
async def test_auth():
    """Endpoint di test per l'autenticazione"""
    return {"message": "Auth API funziona correttamente!", "version": "1.0.0"} 