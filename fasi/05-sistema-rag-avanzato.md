# 🧠 FASE 05: SISTEMA RAG AVANZATO

## 📋 Panoramica Fase

Implementazione del sistema RAG (Retrieval-Augmented Generation) avanzato con integrazione Qdrant, processamento multi-formato documenti, e algoritmi di ranking intelligente per fornire risposte contestuali accurate.

## 🎯 Obiettivi

- **RAG Pipeline Completa**: Indexing, retrieval, ranking e generation
- **Multi-Format Support**: PDF, DOCX, XLSX, TXT, HTML, DWG, PSD, EML
- **Intelligent Chunking**: Strategie avanzate di suddivisione documenti
- **Semantic Search**: Ricerca semantica con embedding avanzati
- **Quality Scoring**: Sistema di scoring per relevance

## ⏱️ Timeline

- **Durata Stimata**: 12-15 giorni
- **Priorità**: ⭐⭐⭐ CRITICA
- **Dipendenze**: Fase 02 (Backend Core), Fase 04 (Sistema Chat AI)
- **Blocca**: Fase 07 (Sistema Indicizzazione)

## 🛠️ Task Dettagliati

### 1. Document Processing Pipeline

- [ ] **Multi-Format Document Processor**
  ```python
  # backend/app/services/document_processor.py
  from abc import ABC, abstractmethod
  from typing import List, Dict, Any
  import fitz  # PyMuPDF for PDF
  import docx2txt  # For DOCX
  import pandas as pd  # For XLSX
  import zipfile
  from bs4 import BeautifulSoup
  import email
  
  class DocumentProcessor(ABC):
      @abstractmethod
      async def extract_text(self, file_path: str) -> str:
          pass
      
      @abstractmethod
      async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
          pass
  
  class PDFProcessor(DocumentProcessor):
      async def extract_text(self, file_path: str) -> str:
          text = ""
          doc = fitz.open(file_path)
          for page in doc:
              text += page.get_text()
          doc.close()
          return text
      
      async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
          doc = fitz.open(file_path)
          metadata = doc.metadata
          doc.close()
          return {
              "title": metadata.get("title", ""),
              "author": metadata.get("author", ""),
              "subject": metadata.get("subject", ""),
              "creator": metadata.get("creator", ""),
              "pages": doc.page_count,
              "format": "PDF"
          }
  
  class DOCXProcessor(DocumentProcessor):
      async def extract_text(self, file_path: str) -> str:
          return docx2txt.process(file_path)
      
      async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
          doc = docx.Document(file_path)
          core_props = doc.core_properties
          return {
              "title": core_props.title or "",
              "author": core_props.author or "",
              "subject": core_props.subject or "",
              "created": core_props.created,
              "modified": core_props.modified,
              "format": "DOCX"
          }
  
  class XLSXProcessor(DocumentProcessor):
      async def extract_text(self, file_path: str) -> str:
          df = pd.read_excel(file_path, sheet_name=None)
          text_content = []
          for sheet_name, sheet_df in df.items():
              text_content.append(f"Sheet: {sheet_name}")
              text_content.append(sheet_df.to_string())
          return "\n\n".join(text_content)
      
      async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
          xl_file = pd.ExcelFile(file_path)
          return {
              "sheets": xl_file.sheet_names,
              "sheet_count": len(xl_file.sheet_names),
              "format": "XLSX"
          }
  
  class HTMLProcessor(DocumentProcessor):
      async def extract_text(self, file_path: str) -> str:
          with open(file_path, 'r', encoding='utf-8') as file:
              soup = BeautifulSoup(file.read(), 'html.parser')
              return soup.get_text()
      
      async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
          with open(file_path, 'r', encoding='utf-8') as file:
              soup = BeautifulSoup(file.read(), 'html.parser')
              title = soup.find('title')
              meta_desc = soup.find('meta', attrs={'name': 'description'})
              return {
                  "title": title.string if title else "",
                  "description": meta_desc.get('content') if meta_desc else "",
                  "format": "HTML"
              }
  
  class EMLProcessor(DocumentProcessor):
      async def extract_text(self, file_path: str) -> str:
          with open(file_path, 'rb') as file:
              msg = email.message_from_bytes(file.read())
              text_content = []
              
              # Extract subject, from, to
              text_content.append(f"Subject: {msg.get('Subject', '')}")
              text_content.append(f"From: {msg.get('From', '')}")
              text_content.append(f"To: {msg.get('To', '')}")
              text_content.append(f"Date: {msg.get('Date', '')}")
              
              # Extract body
              if msg.is_multipart():
                  for part in msg.walk():
                      if part.get_content_type() == "text/plain":
                          text_content.append(part.get_payload(decode=True).decode())
              else:
                  text_content.append(msg.get_payload(decode=True).decode())
              
              return "\n\n".join(text_content)
  
  class DocumentProcessorFactory:
      @staticmethod
      def get_processor(file_extension: str) -> DocumentProcessor:
          processors = {
              '.pdf': PDFProcessor(),
              '.docx': DOCXProcessor(),
              '.xlsx': XLSXProcessor(),
              '.html': HTMLProcessor(),
              '.htm': HTMLProcessor(),
              '.eml': EMLProcessor(),
              '.txt': TXTProcessor(),
          }
          return processors.get(file_extension.lower())
  ```

- [ ] **Intelligent Text Chunking**
  ```python
  # backend/app/services/chunking_service.py
  import re
  from typing import List, Dict, Tuple
  import tiktoken
  
  class ChunkingStrategy(ABC):
      @abstractmethod
      def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
          pass
  
  class SemanticChunkingStrategy(ChunkingStrategy):
      def __init__(self, max_chunk_size: int = 512, overlap: int = 50):
          self.max_chunk_size = max_chunk_size
          self.overlap = overlap
          self.tokenizer = tiktoken.get_encoding("cl100k_base")
      
      def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
          # Split by paragraphs first
          paragraphs = text.split('\n\n')
          chunks = []
          current_chunk = ""
          current_tokens = 0
          
          for paragraph in paragraphs:
              paragraph_tokens = len(self.tokenizer.encode(paragraph))
              
              # If paragraph is too long, split it by sentences
              if paragraph_tokens > self.max_chunk_size:
                  sentences = self._split_by_sentences(paragraph)
                  for sentence in sentences:
                      sentence_tokens = len(self.tokenizer.encode(sentence))
                      
                      if current_tokens + sentence_tokens > self.max_chunk_size and current_chunk:
                          chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                          current_chunk = sentence
                          current_tokens = sentence_tokens
                      else:
                          current_chunk += " " + sentence if current_chunk else sentence
                          current_tokens += sentence_tokens
              else:
                  if current_tokens + paragraph_tokens > self.max_chunk_size and current_chunk:
                      chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                      current_chunk = paragraph
                      current_tokens = paragraph_tokens
                  else:
                      current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                      current_tokens += paragraph_tokens
          
          # Add the last chunk
          if current_chunk:
              chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
          
          return chunks
      
      def _split_by_sentences(self, text: str) -> List[str]:
          sentences = re.split(r'(?<=[.!?])\s+', text)
          return [s.strip() for s in sentences if s.strip()]
      
      def _create_chunk(self, text: str, metadata: Dict, chunk_index: int) -> Dict:
          return {
              "text": text.strip(),
              "metadata": {
                  **metadata,
                  "chunk_index": chunk_index,
                  "token_count": len(self.tokenizer.encode(text)),
              }
          }
  
  class FixedSizeChunkingStrategy(ChunkingStrategy):
      def __init__(self, chunk_size: int = 512, overlap: int = 50):
          self.chunk_size = chunk_size
          self.overlap = overlap
          self.tokenizer = tiktoken.get_encoding("cl100k_base")
      
      def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
          tokens = self.tokenizer.encode(text)
          chunks = []
          
          for i in range(0, len(tokens), self.chunk_size - self.overlap):
              chunk_tokens = tokens[i:i + self.chunk_size]
              chunk_text = self.tokenizer.decode(chunk_tokens)
              
              chunks.append({
                  "text": chunk_text,
                  "metadata": {
                      **metadata,
                      "chunk_index": len(chunks),
                      "token_count": len(chunk_tokens),
                      "start_token": i,
                      "end_token": i + len(chunk_tokens),
                  }
              })
          
          return chunks
  ```

### 2. Qdrant Integration Service

- [ ] **Qdrant Vector Store Service**
  ```python
  # backend/app/services/vector_store_service.py
  from qdrant_client import QdrantClient
  from qdrant_client.models import Distance, VectorParams, PointStruct
  from qdrant_client.models import Filter, FieldCondition, MatchValue
  import uuid
  from typing import List, Dict, Optional, Tuple
  
  class QdrantVectorStore:
      def __init__(self):
          self.client = QdrantClient(
              host=settings.QDRANT_HOST,
              port=settings.QDRANT_PORT,
              api_key=settings.QDRANT_API_KEY,
          )
          self.collection_name = "documents"
          self.embedding_dimension = 3072  # text-embedding-3-large
          
      async def initialize_collection(self):
          """Initialize Qdrant collection if not exists"""
          try:
              collections = await self.client.get_collections()
              if self.collection_name not in [c.name for c in collections.collections]:
                  await self.client.create_collection(
                      collection_name=self.collection_name,
                      vectors_config=VectorParams(
                          size=self.embedding_dimension,
                          distance=Distance.COSINE
                      )
                  )
          except Exception as e:
              logger.error(f"Error initializing Qdrant collection: {e}")
              raise
      
      async def add_documents(
          self,
          chunks: List[Dict],
          embeddings: List[List[float]]
      ) -> List[str]:
          """Add document chunks with embeddings to Qdrant"""
          points = []
          point_ids = []
          
          for chunk, embedding in zip(chunks, embeddings):
              point_id = str(uuid.uuid4())
              point_ids.append(point_id)
              
              points.append(PointStruct(
                  id=point_id,
                  vector=embedding,
                  payload={
                      "text": chunk["text"],
                      "metadata": chunk["metadata"],
                      "document_id": chunk["metadata"].get("document_id"),
                      "file_path": chunk["metadata"].get("file_path"),
                      "chunk_index": chunk["metadata"].get("chunk_index"),
                      "token_count": chunk["metadata"].get("token_count"),
                  }
              ))
          
          try:
              await self.client.upsert(
                  collection_name=self.collection_name,
                  points=points
              )
              return point_ids
          except Exception as e:
              logger.error(f"Error adding documents to Qdrant: {e}")
              raise
      
      async def search_similar(
          self,
          query_embedding: List[float],
          limit: int = 10,
          score_threshold: float = 0.7,
          filters: Optional[Dict] = None
      ) -> List[Tuple[Dict, float]]:
          """Search for similar documents"""
          search_filter = None
          if filters:
              conditions = []
              for key, value in filters.items():
                  conditions.append(FieldCondition(
                      key=key,
                      match=MatchValue(value=value)
                  ))
              search_filter = Filter(must=conditions)
          
          try:
              results = await self.client.search(
                  collection_name=self.collection_name,
                  query_vector=query_embedding,
                  limit=limit,
                  score_threshold=score_threshold,
                  query_filter=search_filter
              )
              
              return [(result.payload, result.score) for result in results]
          except Exception as e:
              logger.error(f"Error searching in Qdrant: {e}")
              raise
      
      async def delete_document(self, document_id: str):
          """Delete all chunks of a document"""
          try:
              await self.client.delete(
                  collection_name=self.collection_name,
                  points_selector=Filter(
                      must=[FieldCondition(
                          key="document_id",
                          match=MatchValue(value=document_id)
                      )]
                  )
              )
          except Exception as e:
              logger.error(f"Error deleting document from Qdrant: {e}")
              raise
      
      async def get_collection_stats(self) -> Dict:
          """Get collection statistics"""
          try:
              info = await self.client.get_collection(self.collection_name)
              return {
                  "total_points": info.points_count,
                  "vector_dimension": info.config.params.vectors.size,
                  "distance_metric": info.config.params.vectors.distance,
              }
          except Exception as e:
              logger.error(f"Error getting collection stats: {e}")
              raise
  ```

### 3. RAG Service Implementation

- [ ] **Main RAG Service**
  ```python
  # backend/app/services/rag_service.py
  from typing import List, Dict, Tuple, Optional
  import asyncio
  from .azure_ai_service import AzureAIService
  from .vector_store_service import QdrantVectorStore
  from .document_processor import DocumentProcessorFactory
  from .chunking_service import SemanticChunkingStrategy
  
  class RAGService:
      def __init__(self):
          self.azure_ai = AzureAIService()
          self.vector_store = QdrantVectorStore()
          self.chunking_strategy = SemanticChunkingStrategy()
          
      async def index_document(
          self,
          file_path: str,
          document_id: str,
          metadata: Optional[Dict] = None
      ) -> Dict:
          """Index a single document"""
          try:
              # 1. Process document
              file_ext = Path(file_path).suffix
              processor = DocumentProcessorFactory.get_processor(file_ext)
              
              if not processor:
                  raise ValueError(f"Unsupported file format: {file_ext}")
              
              text = await processor.extract_text(file_path)
              doc_metadata = await processor.extract_metadata(file_path)
              
              # Merge metadata
              full_metadata = {
                  **doc_metadata,
                  **(metadata or {}),
                  "document_id": document_id,
                  "file_path": file_path,
                  "indexed_at": datetime.utcnow().isoformat(),
              }
              
              # 2. Chunk document
              chunks = self.chunking_strategy.chunk_text(text, full_metadata)
              
              # 3. Generate embeddings
              embeddings = await self._generate_embeddings_batch([chunk["text"] for chunk in chunks])
              
              # 4. Store in vector database
              point_ids = await self.vector_store.add_documents(chunks, embeddings)
              
              return {
                  "document_id": document_id,
                  "chunks_count": len(chunks),
                  "point_ids": point_ids,
                  "status": "indexed",
                  "metadata": full_metadata
              }
              
          except Exception as e:
              logger.error(f"Error indexing document {document_id}: {e}")
              raise
      
      async def query_knowledge_base(
          self,
          query: str,
          conversation_history: List[Dict] = None,
          filters: Optional[Dict] = None,
          max_results: int = 5,
          score_threshold: float = 0.7
      ) -> Tuple[str, List[Dict]]:
          """Query the knowledge base and generate response"""
          try:
              # 1. Generate query embedding
              query_embedding = await self.azure_ai.generate_embedding(query)
              
              # 2. Search similar documents
              search_results = await self.vector_store.search_similar(
                  query_embedding=query_embedding,
                  limit=max_results * 2,  # Get more for re-ranking
                  score_threshold=score_threshold,
                  filters=filters
              )
              
              # 3. Re-rank results based on relevance
              ranked_results = await self._rerank_results(query, search_results)
              top_results = ranked_results[:max_results]
              
              # 4. Prepare context for AI
              context = self._prepare_context(top_results)
              
              # 5. Generate response with RAG
              response = await self._generate_rag_response(
                  query=query,
                  context=context,
                  conversation_history=conversation_history or []
              )
              
              # 6. Prepare sources information
              sources = self._prepare_sources(top_results)
              
              return response, sources
              
          except Exception as e:
              logger.error(f"Error querying knowledge base: {e}")
              # Fallback to general AI response
              fallback_response = await self.azure_ai.generate_response([
                  {"role": "system", "content": "You are a helpful AI assistant."},
                  {"role": "user", "content": query}
              ])
              return fallback_response, []
      
      async def _generate_embeddings_batch(
          self,
          texts: List[str],
          batch_size: int = 10
      ) -> List[List[float]]:
          """Generate embeddings in batches"""
          embeddings = []
          
          for i in range(0, len(texts), batch_size):
              batch = texts[i:i + batch_size]
              batch_embeddings = await asyncio.gather(*[
                  self.azure_ai.generate_embedding(text) for text in batch
              ])
              embeddings.extend(batch_embeddings)
          
          return embeddings
      
      async def _rerank_results(
          self,
          query: str,
          search_results: List[Tuple[Dict, float]]
      ) -> List[Tuple[Dict, float]]:
          """Re-rank search results based on query relevance"""
          # Simple keyword matching for now
          # In production, you might want to use a cross-encoder model
          
          query_words = set(query.lower().split())
          scored_results = []
          
          for result, similarity_score in search_results:
              text = result["text"].lower()
              text_words = set(text.split())
              
              # Calculate keyword overlap
              overlap = len(query_words.intersection(text_words))
              keyword_score = overlap / len(query_words) if query_words else 0
              
              # Combined score (similarity + keyword relevance)
              combined_score = (similarity_score * 0.7) + (keyword_score * 0.3)
              
              scored_results.append((result, combined_score))
          
          # Sort by combined score
          return sorted(scored_results, key=lambda x: x[1], reverse=True)
      
      def _prepare_context(self, results: List[Tuple[Dict, float]]) -> str:
          """Prepare context string from search results"""
          context_parts = []
          
          for i, (result, score) in enumerate(results):
              source_info = f"[Source {i+1}]"
              if "title" in result["metadata"]:
                  source_info += f" {result['metadata']['title']}"
              if "author" in result["metadata"]:
                  source_info += f" by {result['metadata']['author']}"
              
              context_parts.append(f"{source_info}\n{result['text']}\n")
          
          return "\n".join(context_parts)
      
      async def _generate_rag_response(
          self,
          query: str,
          context: str,
          conversation_history: List[Dict]
      ) -> str:
          """Generate response using RAG"""
          system_prompt = f"""You are an AI assistant with access to a knowledge base. 
          Use the provided context to answer the user's question accurately.
          If the context doesn't contain relevant information, say so and provide a general response based on your knowledge.
          
          Context from knowledge base:
          {context}
          """
          
          messages = [{"role": "system", "content": system_prompt}]
          
          # Add conversation history
          messages.extend(conversation_history[-5:])  # Last 5 messages for context
          
          # Add current query
          messages.append({"role": "user", "content": query})
          
          response = await self.azure_ai.generate_response(messages)
          return response
      
      def _prepare_sources(self, results: List[Tuple[Dict, float]]) -> List[Dict]:
          """Prepare sources information for frontend"""
          sources = []
          
          for result, score in results:
              metadata = result["metadata"]
              source = {
                  "title": metadata.get("title", "Unknown Document"),
                  "file_path": metadata.get("file_path", ""),
                  "chunk_index": metadata.get("chunk_index", 0),
                  "score": round(score, 3),
                  "preview": result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"]
              }
              sources.append(source)
          
          return sources
  ```

### 4. Enhanced Chat Integration

- [ ] **Updated Chat Service with RAG**
  ```python
  # backend/app/services/chat_service.py (updated)
  class ChatService:
      def __init__(self):
          self.azure_ai = AzureAIService()
          self.rag_service = RAGService()
          self.db = MongoDB.database
      
      async def send_message_with_rag(
          self,
          session_id: str,
          user_id: str,
          message: str,
          use_rag: bool = True,
          stream: bool = True
      ) -> Union[ChatMessage, AsyncGenerator]:
          """Send message with RAG enhancement"""
          
          # Get conversation history for context
          context = await self.get_conversation_context(session_id, limit=10)
          conversation_history = [
              {"role": "assistant" if not msg.message else "user", 
               "content": msg.response if not msg.message else msg.message}
              for msg in context
          ]
          
          if use_rag:
              # Query knowledge base
              rag_response, sources = await self.rag_service.query_knowledge_base(
                  query=message,
                  conversation_history=conversation_history,
                  max_results=5
              )
              
              if stream:
                  return self.stream_rag_response(
                      session_id, user_id, message, rag_response, sources
                  )
              else:
                  return await self.save_chat_message_with_sources(
                      session_id, user_id, message, rag_response, sources
                  )
          else:
              # Fallback to regular AI response
              messages = conversation_history + [{"role": "user", "content": message}]
              response = await self.azure_ai.generate_response(messages)
              
              return await self.save_chat_message(session_id, user_id, message, response)
      
      async def stream_rag_response(
          self,
          session_id: str,
          user_id: str,
          user_message: str,
          rag_response: str,
          sources: List[Dict]
      ) -> AsyncGenerator[str, None]:
          """Stream RAG response"""
          
          # First send sources
          yield json.dumps({
              "type": "sources",
              "sources": sources,
              "session_id": session_id
          })
          
          # Then stream the response word by word for better UX
          words = rag_response.split()
          full_response = ""
          
          for i, word in enumerate(words):
              full_response += word + " "
              yield json.dumps({
                  "type": "chunk",
                  "content": word + " ",
                  "session_id": session_id
              })
              
              # Small delay for natural typing effect
              await asyncio.sleep(0.05)
          
          # Save complete message with sources
          message = await self.save_chat_message_with_sources(
              session_id, user_id, user_message, full_response.strip(), sources
          )
          
          yield json.dumps({
              "type": "complete",
              "session_id": session_id,
              "message_id": str(message.id)
          })
      
      async def save_chat_message_with_sources(
          self,
          session_id: str,
          user_id: str,
          user_message: str,
          ai_response: str,
          sources: List[Dict]
      ) -> ChatMessage:
          """Save chat message with sources"""
          
          message = ChatMessage(
              session_id=session_id,
              user_id=ObjectId(user_id),
              message=user_message,
              response=ai_response,
              sources=sources,
              metadata={
                  "rag_enabled": True,
                  "sources_count": len(sources),
                  "response_length": len(ai_response)
              }
          )
          
          result = await self.db.chat_messages.insert_one(message.dict(by_alias=True))
          message.id = result.inserted_id
          
          # Update session message count
          await self.db.chat_sessions.update_one(
              {"_id": ObjectId(session_id)},
              {
                  "$inc": {"message_count": 1},
                  "$set": {"updated_at": datetime.utcnow()}
              }
          )
          
          return message
  ```

## 📦 Deliverable

### Document Processing
- [ ] Multi-format document processors (PDF, DOCX, XLSX, etc.)
- [ ] Intelligent chunking strategies
- [ ] Metadata extraction pipelines
- [ ] Error handling per format types

### Vector Store Integration
- [ ] Qdrant collection management
- [ ] Batch embedding operations
- [ ] Similarity search with filters
- [ ] Document deletion and updates

### RAG Pipeline
- [ ] End-to-end RAG implementation
- [ ] Query processing e ranking
- [ ] Context preparation for AI
- [ ] Response generation with sources

### Enhanced Chat
- [ ] RAG-enabled chat responses
- [ ] Source attribution in UI
- [ ] Fallback to general knowledge
- [ ] Performance optimization

## ✅ Criteri di Completamento

### Funzionali
- ✅ Multi-format document processing
- ✅ Vector search con score > 0.7 accuracy
- ✅ RAG responses with relevant sources
- ✅ Fallback mechanism operativo

### Performance
- ✅ Embedding generation < 2s per documento
- ✅ Search latency < 500ms
- ✅ Memory usage ottimizzato per large docs
- ✅ Concurrent processing support

### Quality
- ✅ Response relevance > 85%
- ✅ Source attribution accuracy
- ✅ Error handling robusto
- ✅ Logging completo per debug

## 🚨 Rischi e Mitigazioni

### Rischi Tecnici
- **Embedding Costs**: Batch processing e caching
- **Vector Store Performance**: Index optimization
- **Large Document Processing**: Streaming e chunking
- **Quality Control**: Automated testing pipelines

### Rischi di Qualità
- **Hallucination**: Source verification
- **Context Relevance**: Re-ranking algorithms
- **Response Quality**: A/B testing with users

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: AI & Search Team*