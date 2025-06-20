"""
API Routes per gestione utenti
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
import structlog
from bson import ObjectId

from app.config import settings
from app.core import get_mongodb, log_security_event
from app.models import (
    UserResponse,
    UserUpdate,
    UserList,
    PasswordChange,
    UserRole,
    user_helper,
    PyObjectId
)
from app.core.advanced_logging import log_security_event
from app.api.v1.auth import get_current_user

# Logger
logger = structlog.get_logger(__name__)

# Router
router = APIRouter()


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency per verificare che l'utente sia admin"""
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso riservato agli amministratori"
        )
    return current_user


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user)
):
    """Ottieni il proprio profilo utente"""
    
    try:
        return UserResponse(**user_helper(current_user))
    except Exception as e:
        logger.error("Errore recupero profilo", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Aggiorna il proprio profilo utente"""
    
    try:
        # Prepara campi da aggiornare
        update_fields = {"updated_at": datetime.utcnow()}
        
        if user_update.first_name is not None:
            update_fields["first_name"] = user_update.first_name
        if user_update.last_name is not None:
            update_fields["last_name"] = user_update.last_name
        if user_update.username is not None:
            # Verifica che username non sia già in uso
            existing = await mongodb.users.find_one({
                "username": user_update.username.lower(),
                "_id": {"$ne": current_user["_id"]}
            })
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username già in uso"
                )
            update_fields["username"] = user_update.username.lower()
        
        if user_update.email is not None:
            # Verifica che email non sia già in uso
            existing = await mongodb.users.find_one({
                "email": user_update.email.lower(),
                "_id": {"$ne": current_user["_id"]}
            })
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email già in uso"
                )
            update_fields["email"] = user_update.email.lower()
            update_fields["is_verified"] = False  # Richiede ri-verifica
        
        if user_update.settings is not None:
            update_fields["settings"] = user_update.settings.model_dump()
        
        # Aggiorna database
        result = await mongodb.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_fields}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessuna modifica effettuata"
            )
        
        # Log evento
        await log_security_event(
            user_id=str(current_user["_id"]),
            action="profile_updated",
            details={"fields": list(update_fields.keys())},
            ip_address=request.client.host if request.client else None,
            severity="info"
        )
        
        # Recupera utente aggiornato
        updated_user = await mongodb.users.find_one({"_id": current_user["_id"]})
        
        logger.info(
            "Profilo aggiornato",
            user_id=str(current_user["_id"]),
            fields=list(update_fields.keys())
        )
        
        return UserResponse(**user_helper(updated_user))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore aggiornamento profilo", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/me/change-password")
async def change_my_password(
    password_data: PasswordChange,
    request: Request,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Cambia la propria password"""
    
    try:
        from app.core import verify_password, get_password_hash
        from datetime import datetime
        
        # Verifica password corrente
        if not verify_password(password_data.current_password, current_user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password corrente non valida"
            )
        
        # Genera hash nuova password
        new_password_hash = get_password_hash(password_data.new_password)
        
        # Aggiorna database
        await mongodb.users.update_one(
            {"_id": current_user["_id"]},
            {
                "$set": {
                    "password_hash": new_password_hash,
                    "password_changed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log evento
        await log_security_event(
            user_id=str(current_user["_id"]),
            action="password_changed",
            details={},
            ip_address=request.client.host if request.client else None,
            severity="info"
        )
        
        logger.info("Password cambiata", user_id=str(current_user["_id"]))
        
        return {"message": "Password cambiata con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore cambio password", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


# ===== API AMMINISTRATIVE =====

@router.get("/", response_model=UserList)
async def list_users(
    skip: int = Query(0, ge=0, description="Numero utenti da saltare"),
    limit: int = Query(20, ge=1, le=100, description="Limite utenti da restituire"),
    search: Optional[str] = Query(None, description="Cerca per username, email o nome"),
    role: Optional[UserRole] = Query(None, description="Filtra per ruolo"),
    is_active: Optional[bool] = Query(None, description="Filtra per stato attivo"),
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Lista utenti (solo admin)"""
    
    try:
        # Costruisci filtro
        filter_query = {}
        
        if search:
            filter_query["$or"] = [
                {"username": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}}
            ]
        
        if role is not None:
            filter_query["role"] = role.value
        
        if is_active is not None:
            filter_query["is_active"] = is_active
        
        # Conta totale
        total = await mongodb.users.count_documents(filter_query)
        
        # Recupera utenti
        cursor = mongodb.users.find(filter_query)
        cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)
        users = await cursor.to_list(length=limit)
        
        # Converti in response
        user_responses = [UserResponse(**user_helper(user)) for user in users]
        
        return UserList(
            users=user_responses,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
        
    except Exception as e:
        logger.error("Errore lista utenti", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Ottieni dettagli utente specifico (solo admin)"""
    
    try:
        # Trova utente
        user = await mongodb.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        
        return UserResponse(**user_helper(user))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore recupero utente", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    request: Request,
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Aggiorna utente specifico (solo admin)"""
    
    try:
        # Trova utente
        user = await mongodb.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        
        # Prepara campi da aggiornare
        from datetime import datetime
        update_fields = {
            "updated_at": datetime.utcnow(),
            "last_modified_by": current_user["_id"]
        }
        
        if user_update.first_name is not None:
            update_fields["first_name"] = user_update.first_name
        if user_update.last_name is not None:
            update_fields["last_name"] = user_update.last_name
        if user_update.username is not None:
            # Verifica che username non sia già in uso
            existing = await mongodb.users.find_one({
                "username": user_update.username.lower(),
                "_id": {"$ne": ObjectId(user_id)}
            })
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username già in uso"
                )
            update_fields["username"] = user_update.username.lower()
        
        if user_update.email is not None:
            # Verifica che email non sia già in uso
            existing = await mongodb.users.find_one({
                "email": user_update.email.lower(),
                "_id": {"$ne": ObjectId(user_id)}
            })
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email già in uso"
                )
            update_fields["email"] = user_update.email.lower()
            update_fields["is_verified"] = False  # Richiede ri-verifica
        
        if user_update.role is not None:
            # Solo super admin può modificare ruoli admin
            if (user["role"] in [UserRole.SUPER_ADMIN, UserRole.ADMIN] and 
                current_user["role"] != UserRole.SUPER_ADMIN):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo super admin può modificare ruoli amministrativi"
                )
            update_fields["role"] = user_update.role.value
        
        if user_update.is_active is not None:
            update_fields["is_active"] = user_update.is_active
        
        if user_update.is_verified is not None:
            update_fields["is_verified"] = user_update.is_verified
        
        if user_update.settings is not None:
            update_fields["settings"] = user_update.settings.model_dump()
        
        # Aggiorna database
        result = await mongodb.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessuna modifica effettuata"
            )
        
        # Log evento
        await log_security_event(
            user_id=str(current_user["_id"]),
            action="user_updated",
            details={
                "target_user_id": user_id,
                "fields": list(update_fields.keys())
            },
            ip_address=request.client.host if request.client else None,
            severity="info"
        )
        
        # Recupera utente aggiornato
        updated_user = await mongodb.users.find_one({"_id": ObjectId(user_id)})
        
        logger.info(
            "Utente aggiornato da admin",
            admin_id=str(current_user["_id"]),
            target_user_id=user_id,
            fields=list(update_fields.keys())
        )
        
        return UserResponse(**user_helper(updated_user))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore aggiornamento utente", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(require_admin),
    mongodb = Depends(get_mongodb)
):
    """Elimina utente specifico (solo admin)"""
    
    try:
        # Trova utente
        user = await mongodb.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utente non trovato"
            )
        
        # Non permettere eliminazione di se stessi
        if str(user["_id"]) == str(current_user["_id"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Non puoi eliminare il tuo account"
            )
        
        # Solo super admin può eliminare admin
        if (user["role"] in [UserRole.SUPER_ADMIN, UserRole.ADMIN] and 
            current_user["role"] != UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo super admin può eliminare amministratori"
            )
        
        # Elimina utente (soft delete - disattiva invece di eliminare)
        from datetime import datetime
        await mongodb.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow(),
                    "last_modified_by": current_user["_id"]
                }
            }
        )
        
        # Log evento
        await log_security_event(
            user_id=str(current_user["_id"]),
            action="user_deleted",
            details={"target_user_id": user_id},
            ip_address=request.client.host if request.client else None,
            severity="warning"
        )
        
        logger.info(
            "Utente eliminato da admin",
            admin_id=str(current_user["_id"]),
            target_user_id=user_id
        )
        
        return {"message": "Utente eliminato con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore eliminazione utente", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        ) 