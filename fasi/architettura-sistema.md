# 🏗️ ARCHITETTURA DEL SISTEMA

## 📋 Overview Architetturale

Documentazione completa dell'architettura del portale web aziendale full-stack, includendo pattern architetturali, componenti principali, flussi di dati e decisioni tecniche.

## 🎯 Principi Architetturali

### Scalabilità
- **Microservices-ready**: Architettura modulare facilmente scalabile
- **Horizontal Scaling**: Support per load balancing e clustering
- **Caching Strategy**: Multi-layer caching (Redis, browser, CDN)
- **Database Sharding**: Preparato per partitioning MongoDB

### Resilienza
- **Fault Tolerance**: Graceful degradation e circuit breakers
- **Health Checks**: Monitoring continuo stato servizi
- **Backup Strategy**: Automated backup e disaster recovery
- **Rollback Capability**: Zero-downtime deployment con rollback

### Sicurezza
- **Defense in Depth**: Multiple layer di sicurezza
- **Zero Trust**: Verificazione continua identità e autorizzazioni
- **Data Encryption**: Encryption at rest e in transit
- **Audit Trail**: Logging completo per compliance

## 🔧 Architettura Tecnica

### High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        MOBILE[Mobile App]
    end
    
    subgraph "CDN/Load Balancer"
        CDN[Content Delivery Network]
        LB[Load Balancer]
    end
    
    subgraph "Frontend Layer"
        REACT[React Frontend]
        NGINX[Nginx Server]
    end
    
    subgraph "API Gateway"
        GATEWAY[API Gateway]
        AUTH[Authentication Service]
    end
    
    subgraph "Backend Services"
        API[FastAPI Backend]
        CHAT[Chat Service]
        RAG[RAG Service]
        INDEX[Indexing Service]
        ADMIN[Admin Service]
    end
    
    subgraph "AI Services"
        AZURE[Azure OpenAI]
        EMBEDDING[Embedding Service]
    end
    
    subgraph "Data Layer"
        MONGO[(MongoDB)]
        QDRANT[(Qdrant Vector DB)]
        REDIS[(Redis Cache)]
    end
    
    subgraph "Monitoring"
        GRAFANA[Grafana]
        LOKI[Loki]
        PROMTAIL[Promtail]
    end
    
    WEB --> CDN
    MOBILE --> CDN
    CDN --> LB
    LB --> NGINX
    NGINX --> REACT
    REACT --> GATEWAY
    GATEWAY --> AUTH
    AUTH --> API
    API --> CHAT
    API --> RAG
    API --> INDEX
    API --> ADMIN
    RAG --> AZURE
    RAG --> EMBEDDING
    CHAT --> MONGO
    RAG --> QDRANT
    INDEX --> MONGO
    ADMIN --> MONGO
    API --> REDIS
    API --> GRAFANA
    PROMTAIL --> LOKI
    LOKI --> GRAFANA
```

### Component Architecture

#### Frontend Architecture
```
src/
├── components/
│   ├── ui/              # Reusable UI components (Fluent UI)
│   ├── chat/            # Chat-specific components
│   ├── admin/           # Admin panel components
│   ├── auth/            # Authentication components
│   └── shared/          # Shared business components
├── hooks/               # Custom React hooks
├── store/               # State management (Zustand)
├── services/            # API services e HTTP clients
├── utils/               # Utility functions
├── types/               # TypeScript type definitions
└── contexts/            # React contexts
```

#### Backend Architecture
```
backend/
├── app/
│   ├── api/             # FastAPI routes
│   │   ├── auth/        # Authentication endpoints
│   │   ├── chat/        # Chat endpoints
│   │   ├── admin/       # Admin endpoints
│   │   └── health/      # Health check endpoints
│   ├── core/            # Core functionality
│   │   ├── database.py  # Database connections
│   │   ├── security.py  # Security utilities
│   │   └── config.py    # Configuration management
│   ├── models/          # Pydantic models
│   ├── services/        # Business logic services
│   │   ├── chat_service.py
│   │   ├── rag_service.py
│   │   ├── auth_service.py
│   │   └── admin_service.py
│   ├── middleware/      # Custom middleware
│   └── utils/           # Utility functions
├── tests/               # Test suite
└── alembic/             # Database migrations (if needed)
```

## 🔄 Data Flow Architecture

### Chat Flow
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as Backend API
    participant AI as Azure OpenAI
    participant V as Qdrant
    participant M as MongoDB
    
    U->>F: Send message
    F->>API: POST /chat/message
    API->>M: Save user message
    API->>V: Search similar docs
    V-->>API: Return relevant chunks
    API->>AI: Generate response with context
    AI-->>API: Return AI response
    API->>M: Save AI response
    API-->>F: Stream response
    F-->>U: Display response
```

### Indexing Flow
```mermaid
sequenceDiagram
    participant A as Admin
    participant API as Backend API
    participant IDX as Indexing Service
    participant PROC as Document Processor
    participant AI as Azure OpenAI
    participant V as Qdrant
    participant M as MongoDB
    
    A->>API: Start indexing job
    API->>IDX: Create indexing job
    IDX->>PROC: Process documents
    PROC->>PROC: Extract text & metadata
    PROC->>AI: Generate embeddings
    AI-->>PROC: Return embeddings
    PROC->>V: Store vectors
    PROC->>M: Store metadata
    IDX-->>API: Update job status
    API-->>A: Return job progress
```

## 🗃️ Database Design

### MongoDB Collections

#### Users Collection
```json
{
  "_id": "ObjectId",
  "email": "string",
  "username": "string", 
  "full_name": "string",
  "hashed_password": "string",
  "role": "admin|user|viewer",
  "is_active": "boolean",
  "is_verified": "boolean",
  "mfa_enabled": "boolean",
  "mfa_secret": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Chat Sessions Collection
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "title": "string",
  "message_count": "number",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Chat Messages Collection
```json
{
  "_id": "ObjectId",
  "session_id": "ObjectId",
  "user_id": "ObjectId",
  "message": "string",
  "response": "string",
  "sources": "array",
  "metadata": "object",
  "created_at": "datetime"
}
```

### Qdrant Vector Store Schema
```python
{
  "id": "uuid",
  "vector": [float],  # 3072 dimensions for text-embedding-3-large
  "payload": {
    "text": "string",
    "document_id": "string",
    "file_path": "string",
    "chunk_index": "number",
    "metadata": "object"
  }
}
```

## 🔐 Security Architecture

### Authentication Flow
```mermaid
graph LR
    A[User Login] --> B{Credentials Valid?}
    B -->|Yes| C{MFA Enabled?}
    B -->|No| D[Return Error]
    C -->|Yes| E[Request MFA Token]
    C -->|No| F[Generate JWT]
    E --> G{MFA Valid?}
    G -->|Yes| F
    G -->|No| D
    F --> H[Set HTTP-Only Cookie]
    H --> I[Redirect to Dashboard]
```

### Authorization Layers
1. **Network Level**: Firewall e VPN access
2. **Application Level**: JWT validation
3. **API Level**: Endpoint-specific permissions
4. **Resource Level**: Ownership e role-based access
5. **Data Level**: Row-level security policies

## 📊 Performance Architecture

### Caching Strategy
```mermaid
graph TB
    subgraph "Caching Layers"
        CDN[CDN Cache<br/>Static Assets]
        BROWSER[Browser Cache<br/>Client-side]
        REDIS[Redis Cache<br/>Session & Data]
        MONGO[MongoDB<br/>Persistent Data]
    end
    
    REQUEST[User Request] --> CDN
    CDN --> BROWSER
    BROWSER --> REDIS
    REDIS --> MONGO
```

### Scaling Strategy
- **Frontend**: CDN + horizontal scaling with load balancer
- **Backend**: Horizontal scaling con container orchestration
- **Database**: Read replicas + potential sharding
- **Vector Store**: Qdrant clustering per large datasets
- **Cache**: Redis cluster con replication

## 🔄 Integration Architecture

### External Services Integration
```mermaid
graph TB
    subgraph "Internal Services"
        BACKEND[Backend API]
        FRONTEND[Frontend App]
    end
    
    subgraph "External Services"
        AZURE[Azure OpenAI]
        EMAIL[Email Service]
        SMS[SMS Provider]
        STORAGE[Cloud Storage]
    end
    
    subgraph "Integration Layer"
        CIRCUIT[Circuit Breaker]
        RETRY[Retry Logic]
        FALLBACK[Fallback Handler]
    end
    
    BACKEND --> CIRCUIT
    CIRCUIT --> AZURE
    CIRCUIT --> EMAIL
    CIRCUIT --> SMS
    CIRCUIT --> STORAGE
    CIRCUIT --> RETRY
    CIRCUIT --> FALLBACK
```

## 📈 Monitoring Architecture

### Observability Stack
```mermaid
graph TB
    subgraph "Application"
        APP[Application Logs]
        METRICS[Custom Metrics]
        TRACES[Distributed Traces]
    end
    
    subgraph "Collection"
        PROMTAIL[Promtail]
        PROMETHEUS[Prometheus]
        JAEGER[Jaeger]
    end
    
    subgraph "Storage"
        LOKI[Loki]
        PROM_STORE[Prometheus Storage]
        TRACE_STORE[Trace Storage]
    end
    
    subgraph "Visualization"
        GRAFANA[Grafana Dashboards]
        ALERTS[Alert Manager]
    end
    
    APP --> PROMTAIL
    METRICS --> PROMETHEUS
    TRACES --> JAEGER
    PROMTAIL --> LOKI
    PROMETHEUS --> PROM_STORE
    JAEGER --> TRACE_STORE
    LOKI --> GRAFANA
    PROM_STORE --> GRAFANA
    TRACE_STORE --> GRAFANA
    GRAFANA --> ALERTS
```

## 🏢 Deployment Architecture

### Container Architecture
```mermaid
graph TB
    subgraph "Container Orchestration"
        LB[Load Balancer]
        
        subgraph "Frontend Pods"
            F1[Frontend-1]
            F2[Frontend-2]
            F3[Frontend-3]
        end
        
        subgraph "Backend Pods"
            B1[Backend-1]
            B2[Backend-2]
            B3[Backend-3]
        end
        
        subgraph "Data Services"
            MONGO[MongoDB Cluster]
            REDIS[Redis Cluster]
            QDRANT[Qdrant Cluster]
        end
        
        subgraph "Monitoring"
            GRAF[Grafana]
            LOKI_POD[Loki]
        end
    end
    
    LB --> F1
    LB --> F2
    LB --> F3
    F1 --> B1
    F2 --> B2
    F3 --> B3
    B1 --> MONGO
    B2 --> REDIS
    B3 --> QDRANT
```

## 📝 Decision Records

### Technology Choices

**Frontend Framework: React + TypeScript**
- **Reason**: Mature ecosystem, strong typing, community support
- **Alternatives**: Vue.js, Angular
- **Trade-offs**: Learning curve vs developer productivity

**Backend Framework: FastAPI**
- **Reason**: Automatic API docs, async support, Python ecosystem
- **Alternatives**: Django, Flask, Node.js
- **Trade-offs**: Python performance vs development speed

**Database: MongoDB + Qdrant**
- **Reason**: Document flexibility + vector search capabilities
- **Alternatives**: PostgreSQL + pgvector
- **Trade-offs**: ACID compliance vs scalability

**UI Library: Microsoft Fluent UI**
- **Reason**: Enterprise design system, accessibility
- **Alternatives**: Material-UI, Ant Design
- **Trade-offs**: Customization vs consistency

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: Solutions Architect Team* 