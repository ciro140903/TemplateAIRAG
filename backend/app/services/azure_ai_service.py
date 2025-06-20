"""
Servizio per integrazione con Azure OpenAI
Gestisce chiamate GPT-4 e text-embedding-3-large
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
import structlog
from openai import AsyncAzureOpenAI
import tiktoken

from app.config import settings, AIConfig
from app.models import AIModelConfig


class AzureAIService:
    """Servizio per integrazione Azure OpenAI"""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self._gpt_client: Optional[AsyncAzureOpenAI] = None
        self._embedding_client: Optional[AsyncAzureOpenAI] = None
        self._encoding = tiktoken.get_encoding("cl100k_base")  # Per conteggio tokens
        
        # Statistiche
        self.stats = {
            "total_requests": 0,
            "total_tokens_used": 0,
            "total_errors": 0,
            "average_response_time": 0.0
        }
    
    @property
    def gpt_client(self) -> AsyncAzureOpenAI:
        """Client per GPT-4 (lazy initialization)"""
        if self._gpt_client is None:
            if not AIConfig.is_gpt_configured():
                raise ValueError("Azure OpenAI GPT non configurato correttamente")
            
            config = AIConfig.get_azure_openai_gpt_config()
            self._gpt_client = AsyncAzureOpenAI(
                azure_endpoint=config["endpoint"],
                api_key=config["api_key"],
                api_version=config["api_version"]
            )
            
            self.logger.info(
                "Client Azure OpenAI GPT inizializzato",
                endpoint=config["endpoint"],
                deployment=config["deployment"],
                api_version=config["api_version"]
            )
        
        return self._gpt_client
    
    @property
    def embedding_client(self) -> AsyncAzureOpenAI:
        """Client per embeddings (lazy initialization)"""
        if self._embedding_client is None:
            if not AIConfig.is_embedding_configured():
                raise ValueError("Azure OpenAI Embedding non configurato correttamente")
            
            config = AIConfig.get_azure_openai_embedding_config()
            self._embedding_client = AsyncAzureOpenAI(
                azure_endpoint=config["endpoint"],
                api_key=config["api_key"],
                api_version=config["api_version"]
            )
            
            self.logger.info(
                "Client Azure OpenAI Embedding inizializzato",
                endpoint=config["endpoint"],
                deployment=config["deployment"],
                api_version=config["api_version"]
            )
        
        return self._embedding_client
    
    def count_tokens(self, text: str) -> int:
        """Conta i token in un testo"""
        try:
            return len(self._encoding.encode(text))
        except Exception as e:
            self.logger.warning("Errore conteggio token", error=str(e))
            # Fallback: stima approssimativa
            return len(text.split()) * 1.3
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        model_config: Optional[AIModelConfig] = None
    ) -> Dict[str, Any]:
        """
        Genera risposta usando GPT-4
        
        Args:
            messages: Lista messaggi conversazione
            temperature: Creatività risposta (0.0-1.0)
            max_tokens: Massimo token risposta
            stream: Se True, usa streaming
            model_config: Configurazione modello specifica
            
        Returns:
            Dict con response, usage stats, etc.
        """
        start_time = time.time()
        
        try:
            # Usa configurazione specifica o default
            if model_config:
                deployment = model_config.deployment_name
                temp = model_config.temperature if temperature == 0.7 else temperature
                max_tok = model_config.max_tokens if max_tokens == 2000 else max_tokens
            else:
                gpt_config = AIConfig.get_azure_openai_gpt_config()
                deployment = gpt_config["deployment"]
                temp = temperature
                max_tok = max_tokens
            
            # Log della richiesta
            input_tokens = sum(self.count_tokens(msg.get("content", "")) for msg in messages)
            
            self.logger.info(
                "Generazione risposta GPT-4",
                deployment=deployment,
                temperature=temp,
                max_tokens=max_tok,
                input_tokens=input_tokens,
                messages_count=len(messages)
            )
            
            # Chiamata API
            response = await self.gpt_client.chat.completions.create(
                model=deployment,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                stream=stream,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            processing_time = time.time() - start_time
            
            if stream:
                # Per streaming, ritorna il generatore
                return {
                    "stream": response,
                    "processing_time": processing_time,
                    "input_tokens": input_tokens
                }
            else:
                # Risposta normale
                result = {
                    "content": response.choices[0].message.content,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "processing_time": processing_time,
                    "model": deployment,
                    "temperature": temp
                }
                
                # Aggiorna statistiche
                self.stats["total_requests"] += 1
                self.stats["total_tokens_used"] += result["usage"]["total_tokens"]
                self.stats["average_response_time"] = (
                    (self.stats["average_response_time"] * (self.stats["total_requests"] - 1) + processing_time) 
                    / self.stats["total_requests"]
                )
                
                self.logger.info(
                    "Risposta GPT-4 generata",
                    processing_time=processing_time,
                    total_tokens=result["usage"]["total_tokens"],
                    finish_reason=result["finish_reason"]
                )
                
                return result
                
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats["total_errors"] += 1
            
            self.logger.error(
                "Errore generazione risposta GPT-4",
                error=str(e),
                processing_time=processing_time,
                deployment=deployment if 'deployment' in locals() else "unknown"
            )
            
            raise Exception(f"Errore Azure OpenAI: {str(e)}")
    
    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model_config: Optional[AIModelConfig] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Genera risposta in streaming
        
        Yields:
            Dict con chunk di risposta e metadati
        """
        try:
            response_data = await self.generate_response(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                model_config=model_config
            )
            
            stream = response_data["stream"]
            chunk_count = 0
            content_chunks = []
            
            async for chunk in stream:
                chunk_count += 1
                
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    content_chunks.append(content)
                    
                    yield {
                        "type": "content",
                        "content": content,
                        "chunk_number": chunk_count,
                        "finish_reason": None
                    }
                
                elif chunk.choices and chunk.choices[0].finish_reason:
                    # Fine dello stream
                    full_content = "".join(content_chunks)
                    output_tokens = self.count_tokens(full_content)
                    
                    yield {
                        "type": "finish",
                        "content": "",
                        "finish_reason": chunk.choices[0].finish_reason,
                        "total_chunks": chunk_count,
                        "processing_time": response_data["processing_time"],
                        "usage": {
                            "prompt_tokens": response_data["input_tokens"],
                            "completion_tokens": output_tokens,
                            "total_tokens": response_data["input_tokens"] + output_tokens
                        }
                    }
                    
                    # Aggiorna statistiche
                    self.stats["total_requests"] += 1
                    self.stats["total_tokens_used"] += response_data["input_tokens"] + output_tokens
                    
                    break
                    
        except Exception as e:
            self.logger.error("Errore streaming GPT-4", error=str(e))
            yield {
                "type": "error",
                "content": "",
                "error": str(e)
            }
    
    async def generate_embedding(
        self,
        text: str,
        model_config: Optional[AIModelConfig] = None
    ) -> List[float]:
        """
        Genera embedding per un testo
        
        Args:
            text: Testo da convertire in embedding
            model_config: Configurazione modello specifica
            
        Returns:
            Lista di float rappresentanti l'embedding
        """
        start_time = time.time()
        
        try:
            # Usa configurazione specifica o default
            if model_config:
                deployment = model_config.deployment_name
            else:
                embedding_config = AIConfig.get_azure_openai_embedding_config()
                deployment = embedding_config["deployment"]
            
            # Prepara testo (rimuove newlines multipli, limita lunghezza)
            clean_text = " ".join(text.split())
            if len(clean_text) > 8000:  # Limite sicurezza per embeddings
                clean_text = clean_text[:8000]
                self.logger.warning("Testo troncato per embedding", original_length=len(text))
            
            tokens = self.count_tokens(clean_text)
            
            self.logger.info(
                "Generazione embedding",
                deployment=deployment,
                text_length=len(clean_text),
                tokens=tokens
            )
            
            # Chiamata API
            response = await self.embedding_client.embeddings.create(
                model=deployment,
                input=clean_text
            )
            
            processing_time = time.time() - start_time
            embedding = response.data[0].embedding
            
            # Log risultato
            self.logger.info(
                "Embedding generato",
                processing_time=processing_time,
                embedding_dimensions=len(embedding),
                tokens_used=response.usage.total_tokens
            )
            
            # Aggiorna statistiche
            self.stats["total_requests"] += 1
            self.stats["total_tokens_used"] += response.usage.total_tokens
            
            return embedding
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats["total_errors"] += 1
            
            self.logger.error(
                "Errore generazione embedding",
                error=str(e),
                processing_time=processing_time,
                text_length=len(text)
            )
            
            raise Exception(f"Errore Azure OpenAI Embedding: {str(e)}")
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 10,
        model_config: Optional[AIModelConfig] = None
    ) -> List[List[float]]:
        """
        Genera embeddings per una lista di testi in batch
        
        Args:
            texts: Lista di testi
            batch_size: Dimensione batch per API calls
            model_config: Configurazione modello specifica
            
        Returns:
            Lista di embeddings
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Processa batch in parallelo
            tasks = [
                self.generate_embedding(text, model_config)
                for text in batch
            ]
            
            batch_embeddings = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Gestisci errori nel batch
            for j, embedding in enumerate(batch_embeddings):
                if isinstance(embedding, Exception):
                    self.logger.error(
                        "Errore embedding in batch",
                        batch_index=i + j,
                        error=str(embedding)
                    )
                    # Embedding zero come fallback
                    embeddings.append([0.0] * 1536)  # Dimensione text-embedding-3-large
                else:
                    embeddings.append(embedding)
            
            # Pausa tra batch per rate limiting
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        self.logger.info(
            "Batch embeddings completato",
            total_texts=len(texts),
            successful_embeddings=len([e for e in embeddings if sum(e) != 0])
        )
        
        return embeddings
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica salute dei servizi Azure OpenAI
        
        Returns:
            Dict con stato di salute
        """
        health = {
            "gpt_service": {"status": "unknown", "response_time": None, "error": None},
            "embedding_service": {"status": "unknown", "response_time": None, "error": None},
            "overall_status": "unknown"
        }
        
        # Test GPT service
        try:
            start_time = time.time()
            test_messages = [{"role": "user", "content": "Hello, this is a health check."}]
            
            response = await self.generate_response(
                messages=test_messages,
                temperature=0.1,
                max_tokens=10
            )
            
            health["gpt_service"]["status"] = "healthy"
            health["gpt_service"]["response_time"] = time.time() - start_time
            
        except Exception as e:
            health["gpt_service"]["status"] = "unhealthy"
            health["gpt_service"]["error"] = str(e)
        
        # Test Embedding service
        try:
            start_time = time.time()
            embedding = await self.generate_embedding("Health check test")
            
            if len(embedding) > 0:
                health["embedding_service"]["status"] = "healthy"
                health["embedding_service"]["response_time"] = time.time() - start_time
            else:
                health["embedding_service"]["status"] = "unhealthy"
                health["embedding_service"]["error"] = "Empty embedding returned"
                
        except Exception as e:
            health["embedding_service"]["status"] = "unhealthy"
            health["embedding_service"]["error"] = str(e)
        
        # Determina stato generale
        if (health["gpt_service"]["status"] == "healthy" and 
            health["embedding_service"]["status"] == "healthy"):
            health["overall_status"] = "healthy"
        elif (health["gpt_service"]["status"] == "unhealthy" and 
              health["embedding_service"]["status"] == "unhealthy"):
            health["overall_status"] = "unhealthy"
        else:
            health["overall_status"] = "degraded"
        
        # Aggiungi statistiche
        health["statistics"] = self.stats.copy()
        
        return health
    
    def get_stats(self) -> Dict[str, Any]:
        """Ritorna statistiche d'uso del servizio"""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset statistiche"""
        self.stats = {
            "total_requests": 0,
            "total_tokens_used": 0,
            "total_errors": 0,
            "average_response_time": 0.0
        }
        self.logger.info("Statistiche Azure AI Service resettate")


# Istanza globale del servizio
azure_ai_service = AzureAIService() 