"""
Servizio per gestione chat e conversazioni AI
Gestisce sessioni, messaggi, cronologia e integrazione con Azure AI
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
import structlog
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models import (
    ChatSession,
    ChatMessage,
    ChatMessageCreate,
    ChatSessionCreate,
    ChatSessionUpdate,
    MessageFeedback,
    MessageType,
    MessageStatus,
    PyObjectId,
    chat_session_helper,
    chat_message_helper
)
from .azure_ai_service import azure_ai_service


class ChatService:
    """Servizio per gestione chat e conversazioni"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.logger = structlog.get_logger(__name__)
        
        # Statistiche
        self.stats = {
            "total_sessions": 0,
            "total_messages": 0,
            "active_sessions": 0,
            "total_tokens_used": 0,
            "average_response_time": 0.0
        }
    
    async def create_session(
        self,
        user_id: PyObjectId,
        session_data: ChatSessionCreate,
        ip_address: Optional[str] = None
    ) -> Tuple[Optional[ChatSession], str]:
        """
        Crea una nuova sessione di chat
        
        Args:
            user_id: ID utente proprietario
            session_data: Dati sessione da creare
            ip_address: IP address per audit
            
        Returns:
            Tuple (session, error_message)
        """
        try:
            now = datetime.utcnow()
            
            # Prepara documento sessione
            session_doc = {
                "user_id": user_id,
                "title": session_data.title,
                "description": session_data.description,
                "created_at": now,
                "updated_at": now,
                "last_message_at": None,
                "is_active": True,
                "is_archived": False,
                "is_pinned": False,
                "message_count": 0,
                "user_message_count": 0,
                "ai_message_count": 0,
                "total_tokens_used": 0,
                "total_processing_time": 0.0,
                "ai_model": session_data.ai_model,
                "ai_temperature": session_data.ai_temperature,
                "rag_enabled": session_data.rag_enabled,
                "max_context_messages": 20,
                "tags": session_data.tags,
                "metadata": {},
                "shared_with": []
            }
            
            # Inserisci nel database
            result = await self.db.chat_sessions.insert_one(session_doc)
            session_doc["_id"] = result.inserted_id
            
            self.stats["total_sessions"] += 1
            self.stats["active_sessions"] += 1
            
            self.logger.info(
                "Sessione chat creata",
                session_id=str(result.inserted_id),
                user_id=str(user_id),
                title=session_data.title
            )
            
            return ChatSession(**session_doc), ""
            
        except Exception as e:
            self.logger.error("Errore creazione sessione", error=str(e))
            return None, "Errore interno del server"
    
    async def get_user_sessions(
        self,
        user_id: PyObjectId,
        skip: int = 0,
        limit: int = 20,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Ottiene le sessioni di un utente
        
        Args:
            user_id: ID utente
            skip: Numero sessioni da saltare
            limit: Limite sessioni da restituire
            include_archived: Se includere sessioni archiviate
            
        Returns:
            Lista di sessioni
        """
        try:
            # Costruisci filtro
            filter_query = {"user_id": user_id}
            if not include_archived:
                filter_query["is_archived"] = {"$ne": True}
            
            # Query database
            cursor = self.db.chat_sessions.find(filter_query)
            cursor = cursor.sort([("is_pinned", -1), ("updated_at", -1)])
            cursor = cursor.skip(skip).limit(limit)
            
            sessions = await cursor.to_list(length=limit)
            
            return [chat_session_helper(session) for session in sessions]
            
        except Exception as e:
            self.logger.error("Errore recupero sessioni utente", error=str(e))
            return []
    
    async def get_session(
        self,
        session_id: PyObjectId,
        user_id: PyObjectId
    ) -> Optional[Dict[str, Any]]:
        """
        Ottiene una sessione specifica
        
        Args:
            session_id: ID sessione
            user_id: ID utente (per autorizzazione)
            
        Returns:
            Sessione o None se non trovata/autorizzata
        """
        try:
            session = await self.db.chat_sessions.find_one({
                "_id": session_id,
                "$or": [
                    {"user_id": user_id},
                    {"shared_with": user_id}
                ]
            })
            
            if not session:
                return None
            
            return chat_session_helper(session)
            
        except Exception as e:
            self.logger.error("Errore recupero sessione", error=str(e))
            return None
    
    async def update_session(
        self,
        session_id: PyObjectId,
        user_id: PyObjectId,
        update_data: ChatSessionUpdate
    ) -> Tuple[bool, str]:
        """
        Aggiorna una sessione
        
        Args:
            session_id: ID sessione
            user_id: ID utente (per autorizzazione)
            update_data: Dati da aggiornare
            
        Returns:
            Tuple (success, error_message)
        """
        try:
            # Verifica autorizzazione
            session = await self.db.chat_sessions.find_one({
                "_id": session_id,
                "user_id": user_id
            })
            
            if not session:
                return False, "Sessione non trovata o non autorizzata"
            
            # Prepara aggiornamenti
            update_fields = {"updated_at": datetime.utcnow()}
            
            if update_data.title is not None:
                update_fields["title"] = update_data.title
            if update_data.description is not None:
                update_fields["description"] = update_data.description
            if update_data.is_active is not None:
                update_fields["is_active"] = update_data.is_active
            if update_data.is_archived is not None:
                update_fields["is_archived"] = update_data.is_archived
                if update_data.is_archived:
                    self.stats["active_sessions"] = max(0, self.stats["active_sessions"] - 1)
            if update_data.is_pinned is not None:
                update_fields["is_pinned"] = update_data.is_pinned
            if update_data.ai_temperature is not None:
                update_fields["ai_temperature"] = update_data.ai_temperature
            if update_data.rag_enabled is not None:
                update_fields["rag_enabled"] = update_data.rag_enabled
            if update_data.tags is not None:
                update_fields["tags"] = update_data.tags
            
            # Aggiorna database
            await self.db.chat_sessions.update_one(
                {"_id": session_id},
                {"$set": update_fields}
            )
            
            self.logger.info(
                "Sessione aggiornata",
                session_id=str(session_id),
                user_id=str(user_id)
            )
            
            return True, ""
            
        except Exception as e:
            self.logger.error("Errore aggiornamento sessione", error=str(e))
            return False, "Errore interno del server"
    
    async def delete_session(
        self,
        session_id: PyObjectId,
        user_id: PyObjectId
    ) -> Tuple[bool, str]:
        """
        Elimina una sessione e tutti i suoi messaggi
        
        Args:
            session_id: ID sessione
            user_id: ID utente (per autorizzazione)
            
        Returns:
            Tuple (success, error_message)
        """
        try:
            # Verifica autorizzazione
            session = await self.db.chat_sessions.find_one({
                "_id": session_id,
                "user_id": user_id
            })
            
            if not session:
                return False, "Sessione non trovata o non autorizzata"
            
            # Elimina messaggi associati
            await self.db.chat_messages.delete_many({"session_id": session_id})
            
            # Elimina sessione
            await self.db.chat_sessions.delete_one({"_id": session_id})
            
            self.stats["active_sessions"] = max(0, self.stats["active_sessions"] - 1)
            
            self.logger.info(
                "Sessione eliminata",
                session_id=str(session_id),
                user_id=str(user_id)
            )
            
            return True, ""
            
        except Exception as e:
            self.logger.error("Errore eliminazione sessione", error=str(e))
            return False, "Errore interno del server"
    
    async def send_message(
        self,
        user_id: PyObjectId,
        message_data: ChatMessageCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Invia un messaggio e genera risposta AI
        
        Args:
            user_id: ID utente
            message_data: Dati messaggio
            ip_address: IP address per audit
            user_agent: User agent per audit
            
        Returns:
            Tuple (message_response, error_message)
        """
        try:
            session_id = None
            
            # Crea nuova sessione se necessario
            if not message_data.session_id:
                session_create = ChatSessionCreate(
                    title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    description="Nuova conversazione",
                    ai_temperature=message_data.ai_temperature or 0.7,
                    rag_enabled=message_data.rag_enabled
                )
                
                session, error = await self.create_session(user_id, session_create, ip_address)
                if not session:
                    return None, error
                
                session_id = session.id
            else:
                session_id = ObjectId(message_data.session_id)
                
                # Verifica autorizzazione sessione
                session = await self.get_session(session_id, user_id)
                if not session:
                    return None, "Sessione non trovata o non autorizzata"
            
            # Crea messaggio utente
            now = datetime.utcnow()
            user_message_doc = {
                "session_id": session_id,
                "user_id": user_id,
                "message_type": MessageType.USER,
                "content": message_data.content,
                "ai_response": None,
                "ai_model": None,
                "ai_temperature": None,
                "ai_tokens_used": None,
                "created_at": now,
                "updated_at": now,
                "processing_time": None,
                "status": MessageStatus.COMPLETED,
                "error_message": None,
                "sources": [],
                "rag_enabled": message_data.rag_enabled,
                "rag_query": None,
                "feedback": None,
                "metadata": message_data.metadata,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            
            # Inserisci messaggio utente
            user_result = await self.db.chat_messages.insert_one(user_message_doc)
            user_message_doc["_id"] = user_result.inserted_id
            
            # Genera risposta AI
            ai_message_doc = await self._generate_ai_response(
                session_id, user_id, message_data, ip_address, user_agent
            )
            
            if ai_message_doc:
                ai_result = await self.db.chat_messages.insert_one(ai_message_doc)
                ai_message_doc["_id"] = ai_result.inserted_id
                
                # Aggiorna statistiche sessione
                await self._update_session_stats(
                    session_id, 
                    ai_message_doc.get("ai_tokens_used", 0),
                    ai_message_doc.get("processing_time", 0.0)
                )
            
            self.stats["total_messages"] += 2 if ai_message_doc else 1
            
            # Ritorna il messaggio AI se presente, altrimenti quello utente
            response_message = ai_message_doc or user_message_doc
            
            return chat_message_helper(response_message), ""
            
        except Exception as e:
            self.logger.error("Errore invio messaggio", error=str(e))
            return None, "Errore interno del server"
    
    async def _generate_ai_response(
        self,
        session_id: PyObjectId,
        user_id: PyObjectId,
        message_data: ChatMessageCreate,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Genera risposta AI per un messaggio"""
        try:
            # Ottieni cronologia conversazione
            messages = await self._get_conversation_history(session_id, limit=20)
            
            # Prepara messaggi per AI
            ai_messages = []
            
            # Messaggio di sistema (opzionale)
            ai_messages.append({
                "role": "system",
                "content": "Sei un assistente AI utile e professionale. Rispondi sempre in italiano in modo chiaro e preciso."
            })
            
            # Aggiungi cronologia
            for msg in messages:
                if msg["message_type"] == MessageType.USER:
                    ai_messages.append({
                        "role": "user",
                        "content": msg["content"]
                    })
                elif msg["message_type"] == MessageType.ASSISTANT and msg.get("ai_response"):
                    ai_messages.append({
                        "role": "assistant",
                        "content": msg["ai_response"]
                    })
            
            # Aggiungi messaggio corrente
            ai_messages.append({
                "role": "user",
                "content": message_data.content
            })
            
            # Genera risposta
            start_time = datetime.utcnow()
            
            ai_response = await azure_ai_service.generate_response(
                messages=ai_messages,
                temperature=message_data.ai_temperature or 0.7,
                max_tokens=2000
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Crea documento messaggio AI
            ai_message_doc = {
                "session_id": session_id,
                "user_id": user_id,
                "message_type": MessageType.ASSISTANT,
                "content": message_data.content,  # Messaggio originale utente
                "ai_response": ai_response["content"],
                "ai_model": ai_response["model"],
                "ai_temperature": ai_response["temperature"],
                "ai_tokens_used": ai_response["usage"]["total_tokens"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "processing_time": processing_time,
                "status": MessageStatus.COMPLETED,
                "error_message": None,
                "sources": [],  # TODO: Implementare RAG
                "rag_enabled": message_data.rag_enabled,
                "rag_query": None,
                "feedback": None,
                "metadata": message_data.metadata,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
            
            self.stats["total_tokens_used"] += ai_response["usage"]["total_tokens"]
            
            return ai_message_doc
            
        except Exception as e:
            self.logger.error("Errore generazione risposta AI", error=str(e))
            
            # Crea messaggio di errore
            return {
                "session_id": session_id,
                "user_id": user_id,
                "message_type": MessageType.ERROR,
                "content": message_data.content,
                "ai_response": "Spiacente, si è verificato un errore durante la generazione della risposta.",
                "ai_model": None,
                "ai_temperature": None,
                "ai_tokens_used": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "processing_time": 0.0,
                "status": MessageStatus.FAILED,
                "error_message": str(e),
                "sources": [],
                "rag_enabled": False,
                "rag_query": None,
                "feedback": None,
                "metadata": message_data.metadata,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
    
    async def _get_conversation_history(
        self,
        session_id: PyObjectId,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Ottiene cronologia conversazione per una sessione"""
        try:
            cursor = self.db.chat_messages.find({"session_id": session_id})
            cursor = cursor.sort("created_at", 1).limit(limit)
            
            messages = await cursor.to_list(length=limit)
            return messages
            
        except Exception as e:
            self.logger.error("Errore recupero cronologia", error=str(e))
            return []
    
    async def _update_session_stats(
        self,
        session_id: PyObjectId,
        tokens_used: int,
        processing_time: float
    ):
        """Aggiorna statistiche di una sessione"""
        try:
            await self.db.chat_sessions.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "updated_at": datetime.utcnow(),
                        "last_message_at": datetime.utcnow()
                    },
                    "$inc": {
                        "message_count": 2,  # Messaggio utente + risposta AI
                        "user_message_count": 1,
                        "ai_message_count": 1,
                        "total_tokens_used": tokens_used,
                        "total_processing_time": processing_time
                    }
                }
            )
            
        except Exception as e:
            self.logger.error("Errore aggiornamento statistiche sessione", error=str(e))
    
    async def get_session_messages(
        self,
        session_id: PyObjectId,
        user_id: PyObjectId,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Ottiene messaggi di una sessione
        
        Args:
            session_id: ID sessione
            user_id: ID utente (per autorizzazione)
            skip: Numero messaggi da saltare
            limit: Limite messaggi da restituire
            
        Returns:
            Lista di messaggi
        """
        try:
            # Verifica autorizzazione
            session = await self.get_session(session_id, user_id)
            if not session:
                return []
            
            # Query messaggi
            cursor = self.db.chat_messages.find({"session_id": session_id})
            cursor = cursor.sort("created_at", 1).skip(skip).limit(limit)
            
            messages = await cursor.to_list(length=limit)
            
            return [chat_message_helper(msg) for msg in messages]
            
        except Exception as e:
            self.logger.error("Errore recupero messaggi sessione", error=str(e))
            return []
    
    async def add_message_feedback(
        self,
        message_id: PyObjectId,
        user_id: PyObjectId,
        feedback: MessageFeedback
    ) -> Tuple[bool, str]:
        """
        Aggiunge feedback a un messaggio
        
        Args:
            message_id: ID messaggio
            user_id: ID utente (per autorizzazione)
            feedback: Feedback da aggiungere
            
        Returns:
            Tuple (success, error_message)
        """
        try:
            # Verifica che il messaggio appartenga all'utente
            message = await self.db.chat_messages.find_one({
                "_id": message_id,
                "user_id": user_id
            })
            
            if not message:
                return False, "Messaggio non trovato o non autorizzato"
            
            # Aggiorna feedback
            await self.db.chat_messages.update_one(
                {"_id": message_id},
                {
                    "$set": {
                        "feedback": feedback.model_dump(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            self.logger.info(
                "Feedback messaggio aggiunto",
                message_id=str(message_id),
                user_id=str(user_id),
                feedback_type=feedback.type
            )
            
            return True, ""
            
        except Exception as e:
            self.logger.error("Errore aggiunta feedback", error=str(e))
            return False, "Errore interno del server"
    
    def get_stats(self) -> Dict[str, Any]:
        """Ritorna statistiche del servizio"""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset statistiche"""
        self.stats = {
            "total_sessions": 0,
            "total_messages": 0,
            "active_sessions": 0,
            "total_tokens_used": 0,
            "average_response_time": 0.0
        }
        self.logger.info("Statistiche Chat Service resettate") 