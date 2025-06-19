# ⚙️ FASE 02: BACKEND CORE

## 📋 Panoramica Fase

Sviluppo del backend core in Python con API REST complete, sistema di autenticazione, gestione database MongoDB, e integrazione di base con Azure AI.

## 🎯 Obiettivi

- **API REST Complete**: Endpoints per tutte le funzionalità core
- **Autenticazione Robusta**: JWT + Session management
- **Database Integration**: ODM MongoDB con modelli completi
- **Azure AI Integration**: Connessione e gestione API Azure
- **Logging Strutturato**: Sistema di logging avanzato

## ⏱️ Timeline

- **Durata Stimata**: 8-10 giorni
- **Priorità**: ⭐⭐⭐ CRITICA
- **Dipendenze**: Fase 01 (Setup Infrastrutturale)
- **Parallelo con**: Fase 03 (Frontend Base)

## 🛠️ Task Dettagliati

### 1. Struttura Backend e Framework

- [ ] **Setup FastAPI Project**
  ```
  backend/
  ├── app/
  │   ├── api/
  │   │   ├── v1/
  │   │   │   ├── auth/
  │   │   │   ├── users/
  │   │   │   ├── chat/
  │   │   │   └── admin/
  │   │   └── dependencies.py
  │   ├── core/
  │   │   ├── config.py
  │   │   ├── security.py
  │   │   └── database.py
  │   ├── models/
  │   │   ├── user.py
  │   │   ├── chat.py
  │   │   └── config.py
  │   ├── services/
  │   │   ├── auth_service.py
  │   │   ├── chat_service.py
  │   │   └── azure_ai_service.py
  │   └── main.py
  ├── requirements.txt
  └── Dockerfile
  ```

- [ ] **Dependencies Setup**
  ```python
  # requirements.txt
  fastapi==0.104.1
  uvicorn==0.24.0
  motor==3.3.2          # MongoDB async driver
  pydantic==2.5.0
  python-jose[cryptography]==3.3.0
  passlib[bcrypt]==1.7.4
  python-multipart==0.0.6
  openai==1.3.0         # Azure OpenAI
  qdrant-client==1.7.0
  structlog==23.2.0     # Structured logging
  ```

### 2. Core Configuration & Settings

- [ ] **Configuration Management**
  ```python
  # app/core/config.py
  class Settings(BaseSettings):
      # Database
      MONGODB_URL: str
      DATABASE_NAME: str
      
      # Security
      SECRET_KEY: str
      ALGORITHM: str = "HS256"
      ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
      
      # Azure AI
      AZURE_OPENAI_ENDPOINT: str
      AZURE_OPENAI_API_KEY: str
      AZURE_OPENAI_VERSION: str = "2023-12-01-preview"
      
      # Qdrant
      QDRANT_HOST: str
      QDRANT_PORT: int = 6333
      QDRANT_API_KEY: Optional[str] = None
      
      class Config:
          env_file = ".env"
  ```

- [ ] **Database Connection**
  ```python
  # app/core/database.py
  class MongoDB:
      client: AsyncIOMotorClient = None
      database: AsyncIOMotorDatabase = None
      
      async def connect_to_mongo():
          MongoDB.client = AsyncIOMotorClient(settings.MONGODB_URL)
          MongoDB.database = MongoDB.client[settings.DATABASE_NAME]
          
      async def close_mongo_connection():
          MongoDB.client.close()
  ```

### 3. Modelli Database (Pydantic + MongoDB)

- [ ] **User Model**
  ```python
  # app/models/user.py
  class UserRole(str, Enum):
      ADMIN = "admin"
      USER = "user"
      VIEWER = "viewer"
  
  class User(BaseModel):
      id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
      email: EmailStr
      username: str
      full_name: str
      hashed_password: str
      role: UserRole = UserRole.USER
      is_active: bool = True
      is_verified: bool = False
      mfa_enabled: bool = False
      mfa_secret: Optional[str] = None
      created_at: datetime = Field(default_factory=datetime.utcnow)
      last_login: Optional[datetime] = None
      preferences: Dict[str, Any] = Field(default_factory=dict)
  ```

- [ ] **Chat Models**
  ```python
  # app/models/chat.py
  class ChatMessage(BaseModel):
      id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
      session_id: str
      user_id: PyObjectId
      message: str
      response: str
      timestamp: datetime = Field(default_factory=datetime.utcnow)
      sources: List[Dict[str, Any]] = []
      feedback: Optional[Dict[str, Any]] = None
      metadata: Dict[str, Any] = Field(default_factory=dict)
  
  class ChatSession(BaseModel):
      id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
      user_id: PyObjectId
      title: str
      created_at: datetime = Field(default_factory=datetime.utcnow)
      updated_at: datetime = Field(default_factory=datetime.utcnow)
      is_active: bool = True
      message_count: int = 0
  ```

### 4. Sistema Autenticazione e Sicurezza

- [ ] **Security Utilities**
  ```python
  # app/core/security.py
  class SecurityManager:
      def verify_password(plain_password: str, hashed_password: str) -> bool
      def get_password_hash(password: str) -> str
      def create_access_token(data: dict, expires_delta: Optional[timedelta] = None)
      def verify_token(token: str)
      def generate_mfa_secret() -> str
      def verify_mfa_token(secret: str, token: str) -> bool
  ```

- [ ] **Authentication Service**
  ```python
  # app/services/auth_service.py
  class AuthService:
      async def authenticate_user(email: str, password: str) -> Optional[User]
      async def create_user(user_data: UserCreate) -> User
      async def get_current_user(token: str = Depends(oauth2_scheme)) -> User
      async def verify_mfa(user: User, token: str) -> bool
      async def enable_mfa(user: User) -> str  # Returns QR code
      async def disable_mfa(user: User, token: str) -> bool
  ```

### 5. API Endpoints

- [ ] **Authentication APIs**
  ```python
  # app/api/v1/auth/auth.py
  @router.post("/login")
  async def login(form_data: OAuth2PasswordRequestForm)
  
  @router.post("/register")
  async def register(user_data: UserCreate)
  
  @router.post("/refresh")
  async def refresh_token(refresh_token: str)
  
  @router.post("/mfa/enable")
  async def enable_mfa(current_user: User = Depends(get_current_user))
  
  @router.post("/mfa/verify")
  async def verify_mfa(mfa_data: MFAVerify)
  ```

- [ ] **User Management APIs**
  ```python
  # app/api/v1/users/users.py
  @router.get("/me")
  async def get_current_user_profile(current_user: User = Depends(get_current_user))
  
  @router.put("/me")
  async def update_profile(user_update: UserUpdate, current_user: User = Depends(get_current_user))
  
  @router.get("/", dependencies=[Depends(require_admin)])
  async def list_users(skip: int = 0, limit: int = 100)
  
  @router.put("/{user_id}", dependencies=[Depends(require_admin)])
  async def update_user(user_id: str, user_update: UserUpdate)
  ```

### 6. Azure AI Integration

- [ ] **Azure AI Service**
  ```python
  # app/services/azure_ai_service.py
  class AzureAIService:
      def __init__(self):
          self.client = AzureOpenAI(
              azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
              api_key=settings.AZURE_OPENAI_API_KEY,
              api_version=settings.AZURE_OPENAI_VERSION
          )
      
      async def generate_response(self, messages: List[Dict], stream: bool = False):
          """Generate AI response using GPT-4"""
      
      async def generate_embedding(self, text: str) -> List[float]:
          """Generate embeddings using text-embedding-3-large"""
      
      async def stream_response(self, messages: List[Dict]):
          """Stream AI response for real-time chat"""
  ```

- [ ] **Chat APIs**
  ```python
  # app/api/v1/chat/chat.py
  @router.post("/message")
  async def send_message(
      chat_data: ChatRequest,
      current_user: User = Depends(get_current_user)
  )
  
  @router.get("/sessions")
  async def get_chat_sessions(current_user: User = Depends(get_current_user))
  
  @router.get("/sessions/{session_id}/messages")
  async def get_chat_history(session_id: str, current_user: User = Depends(get_current_user))
  
  @router.websocket("/stream")
  async def chat_stream(websocket: WebSocket, token: str)
  ```

### 7. Sistema Logging Avanzato

- [ ] **Structured Logging Setup**
  ```python
  # app/core/logging.py
  import structlog
  
  def setup_logging():
      structlog.configure(
          processors=[
              structlog.stdlib.filter_by_level,
              structlog.stdlib.add_logger_name,
              structlog.stdlib.add_log_level,
              structlog.stdlib.PositionalArgumentsFormatter(),
              structlog.processors.TimeStamper(fmt="iso"),
              structlog.processors.StackInfoRenderer(),
              structlog.processors.format_exc_info,
              structlog.processors.UnicodeDecoder(),
              structlog.processors.JSONRenderer()
          ],
          context_class=dict,
          logger_factory=structlog.stdlib.LoggerFactory(),
          wrapper_class=structlog.stdlib.BoundLogger,
          cache_logger_on_first_use=True,
      )
  ```

- [ ] **Logging Middleware**
  ```python
  # app/middleware/logging.py
  class LoggingMiddleware:
      async def log_request(request: Request, call_next):
          # Log request details
          # Measure response time
          # Log response status and errors
  ```

### 8. Database Schemas e Migrations

- [ ] **Database Initialization**
  ```python
  # app/db/init_db.py
  async def create_indexes():
      # User indexes
      await db.users.create_index("email", unique=True)
      await db.users.create_index("username", unique=True)
      
      # Chat indexes
      await db.chat_sessions.create_index([("user_id", 1), ("created_at", -1)])
      await db.chat_messages.create_index([("session_id", 1), ("timestamp", 1)])
      
  async def create_default_admin():
      # Create default admin user if not exists
  ```

## 📦 Deliverable

### API Documentation
- [ ] OpenAPI/Swagger documentation completa
- [ ] Postman collection per testing
- [ ] API versioning strategy
- [ ] Rate limiting implementation

### Security Features
- [ ] JWT token management
- [ ] Password hashing e validation
- [ ] MFA implementation base
- [ ] CORS configuration
- [ ] Input validation e sanitization

### Database Layer
- [ ] MongoDB ODM con Pydantic models
- [ ] Database connection management
- [ ] Index optimization
- [ ] Migration scripts

### Monitoring & Logging
- [ ] Structured logging implementato
- [ ] Health check endpoints
- [ ] Metrics collection base
- [ ] Error tracking

## ✅ Criteri di Completamento

### API Funzionali
- ✅ Tutte le API REST sono documentate e testabili
- ✅ Sistema autenticazione JWT funzionante
- ✅ CRUD operations per user management
- ✅ Integration test con Azure AI APIs

### Performance
- ✅ Response time < 500ms per API standard
- ✅ Database queries ottimizzate
- ✅ Connection pooling configurato
- ✅ Memory usage controllato

### Security
- ✅ Password hashing implementato
- ✅ JWT tokens sicuri
- ✅ Input validation su tutti gli endpoints
- ✅ Error handling che non espone info sensibili

## 🚨 Rischi e Mitigazioni

### Rischi Tecnici
- **Azure AI Quotas**: Implementare rate limiting e fallback
- **Database Performance**: Monitoring queries e index tuning
- **Authentication Complexity**: Test approfonditi per security

### Rischi di Progetto
- **API Design Changes**: Versionings strategy ben definita
- **Third-party Dependencies**: Pinning versions e dependency audit
- **Integration Issues**: Mock services per testing

## 🔗 Dipendenze

### Esterne
- **Azure OpenAI APIs**: Account e quota configurati
- **MongoDB**: Database operativo dalla Fase 01
- **Python 3.11+**: Runtime environment

### Interne
- **Fase 01**: Infrastruttura Docker funzionante
- **Environment Variables**: Configurazione completa

## 📄 File di Supporto

- **API Tests**: `./tests/api/`
- **Mock Data**: `./tests/fixtures/`
- **Performance Tests**: `./tests/performance/`
- **Security Tests**: `./tests/security/`

---

## 🎯 Prossimi Passi

Al completamento di questa fase:
1. **API Testing Completo**: Validation con frontend team
2. **Performance Tuning**: Ottimizzazione base performance
3. **Security Review**: Audit sicurezza con security team
4. **Integration Testing**: Test integrazione con Fase 03

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: Backend Development Team* 