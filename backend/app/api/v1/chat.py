"""
API Routes per gestione chat e conversazioni AI
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, WebSocket, WebSocketDisconnect
import structlog
from bson import ObjectId

from app.core import get_mongodb
from app.models import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionResponse,
    ChatSessionList,
    ChatMessageCreate,
    ChatMessageResponse,
    MessageFeedbackCreate,
    MessageFeedback,
    chat_session_helper,
    chat_message_helper,
    PyObjectId
)
from app.services.chat_service import ChatService
from app.api.v1.auth import get_current_user

# Logger
logger = structlog.get_logger(__name__)

# Router
router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Crea una nuova sessione di chat"""
    
    try:
        # Crea servizio chat
        chat_service = ChatService(mongodb)
        
        # Crea sessione
        session, error = await chat_service.create_session(
            user_id=current_user["_id"],
            session_data=session_data,
            ip_address=request.client.host if request.client else None
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        logger.info(
            "Sessione chat creata",
            session_id=str(session.id),
            user_id=str(current_user["_id"]),
            title=session.title
        )
        
        return ChatSessionResponse(**chat_session_helper(session.model_dump()))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore creazione sessione chat", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.get("/sessions", response_model=ChatSessionList)
async def get_chat_sessions(
    skip: int = Query(0, ge=0, description="Numero sessioni da saltare"),
    limit: int = Query(20, ge=1, le=50, description="Limite sessioni da restituire"),
    include_archived: bool = Query(False, description="Includi sessioni archiviate"),
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Ottieni le sessioni di chat dell'utente"""
    
    try:
        # Crea servizio chat
        chat_service = ChatService(mongodb)
        
        # Recupera sessioni
        sessions = await chat_service.get_user_sessions(
            user_id=current_user["_id"],
            skip=skip,
            limit=limit,
            include_archived=include_archived
        )
        
        # Conta totale
        filter_query = {"user_id": current_user["_id"]}
        if not include_archived:
            filter_query["is_archived"] = {"$ne": True}
        
        total = await mongodb.chat_sessions.count_documents(filter_query)
        
        return ChatSessionList(
            sessions=[ChatSessionResponse(**session) for session in sessions],
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
        
    except Exception as e:
        logger.error("Errore recupero sessioni chat", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Ottieni dettagli di una sessione specifica"""
    
    try:
        # Crea servizio chat
        chat_service = ChatService(mongodb)
        
        # Recupera sessione
        session = await chat_service.get_session(
            session_id=ObjectId(session_id),
            user_id=current_user["_id"]
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sessione non trovata"
            )
        
        return ChatSessionResponse(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore recupero sessione chat", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: str,
    session_update: ChatSessionUpdate,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Aggiorna una sessione di chat"""
    
    try:
        # Crea servizio chat
        chat_service = ChatService(mongodb)
        
        # Aggiorna sessione
        success, error = await chat_service.update_session(
            session_id=ObjectId(session_id),
            user_id=current_user["_id"],
            update_data=session_update
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        # Recupera sessione aggiornata
        session = await chat_service.get_session(
            session_id=ObjectId(session_id),
            user_id=current_user["_id"]
        )
        
        logger.info(
            "Sessione chat aggiornata",
            session_id=session_id,
            user_id=str(current_user["_id"])
        )
        
        return ChatSessionResponse(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore aggiornamento sessione chat", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Elimina una sessione di chat"""
    
    try:
        # Crea servizio chat
        chat_service = ChatService(mongodb)
        
        # Elimina sessione
        success, error = await chat_service.delete_session(
            session_id=ObjectId(session_id),
            user_id=current_user["_id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        logger.info(
            "Sessione chat eliminata",
            session_id=session_id,
            user_id=str(current_user["_id"])
        )
        
        return {"message": "Sessione eliminata con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore eliminazione sessione chat", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    skip: int = Query(0, ge=0, description="Numero messaggi da saltare"),
    limit: int = Query(50, ge=1, le=100, description="Limite messaggi da restituire"),
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Ottieni messaggi di una sessione"""
    
    try:
        # Crea servizio chat
        chat_service = ChatService(mongodb)
        
        # Recupera messaggi
        messages = await chat_service.get_session_messages(
            session_id=ObjectId(session_id),
            user_id=current_user["_id"],
            skip=skip,
            limit=limit
        )
        
        return {
            "messages": [ChatMessageResponse(**msg) for msg in messages],
            "session_id": session_id,
            "total": len(messages)
        }
        
    except Exception as e:
        logger.error("Errore recupero messaggi sessione", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    message_data: ChatMessageCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Invia un messaggio e ottieni risposta AI"""
    
    try:
        # Crea servizio chat
        chat_service = ChatService(mongodb)
        
        # Invia messaggio
        message_response, error = await chat_service.send_message(
            user_id=current_user["_id"],
            message_data=message_data,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        if not message_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        logger.info(
            "Messaggio inviato",
            user_id=str(current_user["_id"]),
            session_id=message_response.get("session_id"),
            message_length=len(message_data.content)
        )
        
        return ChatMessageResponse(**message_response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore invio messaggio", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


@router.post("/messages/{message_id}/feedback")
async def add_message_feedback(
    message_id: str,
    feedback_data: MessageFeedbackCreate,
    current_user: dict = Depends(get_current_user),
    mongodb = Depends(get_mongodb)
):
    """Aggiungi feedback a un messaggio"""
    
    try:
        # Crea servizio chat
        chat_service = ChatService(mongodb)
        
        # Crea feedback
        feedback = MessageFeedback(
            type=feedback_data.feedback_type,
            value=feedback_data.value,
            comment=feedback_data.comment
        )
        
        # Aggiungi feedback
        success, error = await chat_service.add_message_feedback(
            message_id=ObjectId(message_id),
            user_id=current_user["_id"],
            feedback=feedback
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        logger.info(
            "Feedback messaggio aggiunto",
            message_id=message_id,
            user_id=str(current_user["_id"]),
            feedback_type=feedback_data.feedback_type
        )
        
        return {"message": "Feedback aggiunto con successo"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Errore aggiunta feedback", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server"
        )


# ===== WEBSOCKET PER STREAMING =====

class ConnectionManager:
    """Gestore connessioni WebSocket"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket
        logger.info("WebSocket connesso", user_id=user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        logger.info("WebSocket disconnesso", user_id=user_id)
    
    async def send_personal_message(self, message: dict, user_id: str):
        websocket = self.user_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)


manager = ConnectionManager()


@router.websocket("/stream")
async def chat_stream(
    websocket: WebSocket,
    token: str,
    mongodb = Depends(get_mongodb)
):
    """WebSocket per streaming delle risposte AI"""
    
    # Verifica token
    from app.core import verify_token
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Token non valido")
        return
    
    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Token non valido")
        return
    
    # Trova utente
    user = await mongodb.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("is_active"):
        await websocket.close(code=4001, reason="Utente non valido")
        return
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Ricevi messaggio dal client
            data = await websocket.receive_json()
            
            # Valida dati
            if "content" not in data:
                await websocket.send_json({
                    "type": "error",
                    "error": "Campo 'content' richiesto"
                })
                continue
            
            # Crea servizio chat
            chat_service = ChatService(mongodb)
            
            # Prepara dati messaggio
            message_data = ChatMessageCreate(
                session_id=data.get("session_id"),
                content=data["content"],
                rag_enabled=data.get("rag_enabled", True),
                ai_temperature=data.get("ai_temperature", 0.7),
                metadata=data.get("metadata", {})
            )
            
            # Invia messaggio e stream risposta
            message_response, error = await chat_service.send_message(
                user_id=ObjectId(user_id),
                message_data=message_data,
                ip_address=None,  # WebSocket non ha IP facilmente accessibile
                user_agent=None
            )
            
            if error:
                await websocket.send_json({
                    "type": "error",
                    "error": error
                })
                continue
            
            # Invia risposta
            await websocket.send_json({
                "type": "message",
                "data": message_response
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error("Errore WebSocket chat", error=str(e), user_id=user_id)
        await websocket.send_json({
            "type": "error",
            "error": "Errore interno del server"
        })
        manager.disconnect(websocket, user_id) 