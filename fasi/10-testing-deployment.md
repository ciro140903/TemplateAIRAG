# 🚀 FASE 10: TESTING E DEPLOYMENT

## 📋 Panoramica Fase

Implementazione completa del sistema di testing automatizzato, pipeline CI/CD, deployment strategies, e procedure di production readiness per il portale aziendale.

## 🎯 Obiettivi

- **Testing Automatizzato**: Unit, integration, e2e testing
- **CI/CD Pipeline**: Automated build, test, deploy
- **Production Deployment**: Containerized deployment with orchestration
- **Monitoring & Rollback**: Health checks e rollback procedures
- **Documentation**: Complete deployment e operational docs

## ⏱️ Timeline

- **Durata Stimata**: 8-10 giorni
- **Priorità**: ⭐⭐⭐ CRITICA
- **Dipendenze**: Tutte le fasi precedenti
- **Finalizza**: Progetto completo

## 🛠️ Task Dettagliati

### 1. Backend Testing Infrastructure

- [ ] **Unit Testing Setup**
  ```python
  # backend/tests/conftest.py
  import pytest
  import asyncio
  from httpx import AsyncClient
  from app.main import app
  from app.core.database import MongoDB
  from app.models.user import User
  import mongomock
  
  @pytest.fixture(scope="session")
  def event_loop():
      """Create an instance of the default event loop for the test session."""
      loop = asyncio.get_event_loop_policy().new_event_loop()
      yield loop
      loop.close()
  
  @pytest.fixture
  async def test_client():
      """Create test client"""
      async with AsyncClient(app=app, base_url="http://test") as client:
          yield client
  
  @pytest.fixture
  async def mock_db():
      """Mock database for testing"""
      mock_client = mongomock.MongoClient()
      mock_db = mock_client.test_database
      
      # Patch MongoDB
      original_db = MongoDB.database
      MongoDB.database = mock_db
      
      yield mock_db
      
      # Restore original
      MongoDB.database = original_db
  
  @pytest.fixture
  async def test_user(mock_db):
      """Create test user"""
      user = User(
          email="test@example.com",
          username="testuser",
          full_name="Test User",
          hashed_password="$2b$12$test",
          role="user",
          is_active=True,
          is_verified=True
      )
      result = await mock_db.users.insert_one(user.dict(by_alias=True))
      user.id = result.inserted_id
      return user
  ```

- [ ] **Service Testing**
  ```python
  # backend/tests/test_chat_service.py
  import pytest
  from app.services.chat_service import ChatService
  from app.models.chat import ChatSession, ChatMessage
  
  class TestChatService:
      @pytest.fixture
      def chat_service(self, mock_db):
          return ChatService()
      
      async def test_create_chat_session(self, chat_service, test_user, mock_db):
          """Test chat session creation"""
          session = await chat_service.create_chat_session(
              user_id=str(test_user.id),
              title="Test Session"
          )
          
          assert session.title == "Test Session"
          assert session.user_id == test_user.id
          assert session.message_count == 0
          
          # Verify in database
          db_session = await mock_db.chat_sessions.find_one({"_id": session.id})
          assert db_session is not None
      
      async def test_send_message(self, chat_service, test_user, mock_db):
          """Test message sending"""
          # Create session first
          session = await chat_service.create_chat_session(
              user_id=str(test_user.id),
              title="Test Session"
          )
          
          # Mock AI response
          with patch('app.services.azure_ai_service.AzureAIService.generate_response') as mock_ai:
              mock_ai.return_value = "Test AI response"
              
              message = await chat_service.send_message(
                  session_id=str(session.id),
                  user_id=str(test_user.id),
                  message="Hello AI"
              )
          
          assert message.message == "Hello AI"
          assert message.response == "Test AI response"
          assert message.session_id == session.id
  ```

### 2. Frontend Testing

- [ ] **Component Testing**
  ```typescript
  // src/components/__tests__/ChatInterface.test.tsx
  import { render, screen, fireEvent, waitFor } from '@testing-library/react';
  import { vi } from 'vitest';
  import { ChatInterface } from '../chat/ChatInterface';
  import { ChatProvider } from '@/contexts/ChatContext';
  
  // Mock WebSocket
  const mockWebSocket = {
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };
  
  global.WebSocket = vi.fn(() => mockWebSocket);
  
  const renderWithProvider = (component: React.ReactElement) => {
    return render(
      <ChatProvider>
        {component}
      </ChatProvider>
    );
  };
  
  describe('ChatInterface', () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });
  
    it('renders chat interface correctly', () => {
      renderWithProvider(<ChatInterface />);
      
      expect(screen.getByPlaceholderText('Scrivi un messaggio...')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Invia' })).toBeInTheDocument();
    });
  
    it('sends message when form is submitted', async () => {
      renderWithProvider(<ChatInterface />);
      
      const input = screen.getByPlaceholderText('Scrivi un messaggio...');
      const sendButton = screen.getByRole('button', { name: 'Invia' });
      
      fireEvent.change(input, { target: { value: 'Test message' } });
      fireEvent.click(sendButton);
      
      await waitFor(() => {
        expect(mockWebSocket.send).toHaveBeenCalledWith(
          JSON.stringify({
            type: 'message',
            content: 'Test message',
          })
        );
      });
    });
  
    it('displays messages correctly', async () => {
      const mockMessages = [
        {
          id: '1',
          message: 'Hello',
          response: 'Hi there!',
          timestamp: new Date().toISOString(),
        },
      ];
      
      // Mock store with messages
      vi.mock('@/store/chatStore', () => ({
        useChatStore: () => ({
          messages: mockMessages,
          sendMessage: vi.fn(),
          isLoading: false,
        }),
      }));
      
      renderWithProvider(<ChatInterface />);
      
      expect(screen.getByText('Hello')).toBeInTheDocument();
      expect(screen.getByText('Hi there!')).toBeInTheDocument();
    });
  });
  ```

### 3. CI/CD Pipeline

- [ ] **GitHub Actions Workflow**
  ```yaml
  # .github/workflows/ci-cd.yml
  name: CI/CD Pipeline
  
  on:
    push:
      branches: [main, develop]
    pull_request:
      branches: [main]
  
  env:
    REGISTRY: ghcr.io
    IMAGE_NAME: ${{ github.repository }}
  
  jobs:
    test-backend:
      runs-on: ubuntu-latest
      
      services:
        mongodb:
          image: mongo:6.0
          ports:
            - 27017:27017
        redis:
          image: redis:7-alpine
          ports:
            - 6379:6379
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Python
          uses: actions/setup-python@v4
          with:
            python-version: '3.11'
        
        - name: Install dependencies
          run: |
            cd backend
            pip install -r requirements.txt
            pip install pytest pytest-asyncio pytest-cov
        
        - name: Run tests
          run: |
            cd backend
            pytest --cov=app --cov-report=xml
        
        - name: Upload coverage
          uses: codecov/codecov-action@v3
          with:
            file: ./backend/coverage.xml
  
    test-frontend:
      runs-on: ubuntu-latest
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Node.js
          uses: actions/setup-node@v4
          with:
            node-version: '18'
            cache: 'npm'
            cache-dependency-path: frontend/package-lock.json
        
        - name: Install dependencies
          run: |
            cd frontend
            npm ci
        
        - name: Run linting
          run: |
            cd frontend
            npm run lint
        
        - name: Run tests
          run: |
            cd frontend
            npm run test:coverage
        
        - name: Build application
          run: |
            cd frontend
            npm run build
  
    security-scan:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        
        - name: Run Trivy vulnerability scanner
          uses: aquasecurity/trivy-action@master
          with:
            scan-type: 'fs'
            scan-ref: '.'
            format: 'sarif'
            output: 'trivy-results.sarif'
        
        - name: Upload Trivy scan results
          uses: github/codeql-action/upload-sarif@v2
          with:
            sarif_file: 'trivy-results.sarif'
  
    build-and-push:
      if: github.ref == 'refs/heads/main'
      needs: [test-backend, test-frontend, security-scan]
      runs-on: ubuntu-latest
      
      permissions:
        contents: read
        packages: write
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Set up Docker Buildx
          uses: docker/setup-buildx-action@v3
        
        - name: Log in to Container Registry
          uses: docker/login-action@v3
          with:
            registry: ${{ env.REGISTRY }}
            username: ${{ github.actor }}
            password: ${{ secrets.GITHUB_TOKEN }}
        
        - name: Extract metadata
          id: meta
          uses: docker/metadata-action@v5
          with:
            images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
            tags: |
              type=ref,event=branch
              type=ref,event=pr
              type=sha,prefix={{branch}}-
        
        - name: Build and push Backend
          uses: docker/build-push-action@v5
          with:
            context: ./backend
            push: true
            tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-backend:${{ steps.meta.outputs.tags }}
            labels: ${{ steps.meta.outputs.labels }}
            cache-from: type=gha
            cache-to: type=gha,mode=max
        
        - name: Build and push Frontend
          uses: docker/build-push-action@v5
          with:
            context: ./frontend
            push: true
            tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-frontend:${{ steps.meta.outputs.tags }}
            labels: ${{ steps.meta.outputs.labels }}
            cache-from: type=gha
            cache-to: type=gha,mode=max
  
    deploy-staging:
      if: github.ref == 'refs/heads/develop'
      needs: [build-and-push]
      runs-on: ubuntu-latest
      environment: staging
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Deploy to Staging
          run: |
            echo "Deploying to staging environment..."
            # Add deployment commands here
  
    deploy-production:
      if: github.ref == 'refs/heads/main'
      needs: [build-and-push]
      runs-on: ubuntu-latest
      environment: production
      
      steps:
        - uses: actions/checkout@v4
        
        - name: Deploy to Production
          run: |
            echo "Deploying to production environment..."
            # Add deployment commands here
  ```

### 4. Production Deployment

- [ ] **Production Docker Compose**
  ```yaml
  # docker-compose.prod.yml
  version: '3.8'
  
  services:
    frontend:
      image: ghcr.io/company/portal-frontend:latest
      restart: unless-stopped
      environment:
        - NODE_ENV=production
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.frontend.rule=Host(`portal.company.com`)"
        - "traefik.http.routers.frontend.tls=true"
        - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
      networks:
        - portal_network
    
    backend:
      image: ghcr.io/company/portal-backend:latest
      restart: unless-stopped
      environment:
        - ENV=production
        - MONGODB_URL=${MONGODB_URL}
        - REDIS_URL=${REDIS_URL}
        - AZURE_OPENAI_KEY=${AZURE_OPENAI_KEY}
        - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
        - JWT_SECRET=${JWT_SECRET}
        - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.backend.rule=Host(`api.portal.company.com`)"
        - "traefik.http.routers.backend.tls=true"
        - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
      depends_on:
        - mongodb
        - redis
        - qdrant
      networks:
        - portal_network
      volumes:
        - ./uploads:/app/uploads
        - ./logs:/app/logs
    
    mongodb:
      image: mongo:6.0
      restart: unless-stopped
      environment:
        MONGO_INITDB_ROOT_USERNAME: ${MONGO_USERNAME}
        MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      volumes:
        - mongodb_data:/data/db
        - ./backup:/backup
      networks:
        - portal_network
    
    redis:
      image: redis:7-alpine
      restart: unless-stopped
      command: redis-server --requirepass ${REDIS_PASSWORD}
      volumes:
        - redis_data:/data
      networks:
        - portal_network
    
    qdrant:
      image: qdrant/qdrant:latest
      restart: unless-stopped
      environment:
        QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY}
      volumes:
        - qdrant_data:/qdrant/storage
      networks:
        - portal_network
    
    traefik:
      image: traefik:v3.0
      restart: unless-stopped
      command:
        - "--api.dashboard=true"
        - "--providers.docker=true"
        - "--providers.docker.exposedbydefault=false"
        - "--entrypoints.web.address=:80"
        - "--entrypoints.websecure.address=:443"
        - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
        - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
        - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      ports:
        - "80:80"
        - "443:443"
        - "8080:8080"
      volumes:
        - /var/run/docker.sock:/var/run/docker.sock:ro
        - letsencrypt_data:/letsencrypt
      networks:
        - portal_network
    
    grafana:
      image: grafana/grafana:latest
      restart: unless-stopped
      environment:
        GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
        GF_INSTALL_PLUGINS: grafana-clock-panel,grafana-simple-json-datasource
      volumes:
        - grafana_data:/var/lib/grafana
        - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.grafana.rule=Host(`monitoring.portal.company.com`)"
        - "traefik.http.routers.grafana.tls=true"
      networks:
        - portal_network
    
    loki:
      image: grafana/loki:latest
      restart: unless-stopped
      command: -config.file=/etc/loki/local-config.yaml
      volumes:
        - loki_data:/loki
        - ./monitoring/loki/config.yml:/etc/loki/local-config.yaml
      networks:
        - portal_network
    
    promtail:
      image: grafana/promtail:latest
      restart: unless-stopped
      volumes:
        - ./logs:/var/log
        - ./monitoring/promtail/config.yml:/etc/promtail/config.yml
      networks:
        - portal_network
  
  volumes:
    mongodb_data:
    redis_data:
    qdrant_data:
    grafana_data:
    loki_data:
    letsencrypt_data:
  
  networks:
    portal_network:
      external: true
  ```

### 5. Health Checks & Monitoring

- [ ] **Production Health Endpoints**
  ```python
  # backend/app/api/health.py
  from fastapi import APIRouter, Depends
  from app.services.health_service import HealthCheckService
  
  router = APIRouter(prefix="/health", tags=["health"])
  
  @router.get("/")
  async def basic_health():
      """Basic health check"""
      return {"status": "healthy", "service": "portal-backend"}
  
  @router.get("/detailed")
  async def detailed_health(
      health_service: HealthCheckService = Depends()
  ):
      """Detailed health check with all dependencies"""
      return await health_service.get_system_health()
  
  @router.get("/readiness")
  async def readiness_check(
      health_service: HealthCheckService = Depends()
  ):
      """Readiness probe for Kubernetes/container orchestration"""
      health = await health_service.get_system_health()
      
      if health["status"] == "healthy":
          return {"status": "ready"}
      else:
          raise HTTPException(
              status_code=503,
              detail="Service not ready"
          )
  
  @router.get("/liveness")
  async def liveness_check():
      """Liveness probe - basic service availability"""
      return {"status": "alive"}
  ```

## 📦 Deliverable

### Testing Infrastructure
- [ ] Comprehensive test suites (unit, integration, e2e)
- [ ] Code coverage reporting
- [ ] Automated test execution
- [ ] Performance testing setup

### CI/CD Pipeline
- [ ] Automated build e test pipeline
- [ ] Security scanning integration
- [ ] Multi-environment deployment
- [ ] Rollback capabilities

### Production Setup
- [ ] Production-ready Docker configuration
- [ ] Load balancer e reverse proxy setup
- [ ] SSL/TLS certificate management
- [ ] Backup e disaster recovery procedures

### Monitoring & Observability
- [ ] Health check endpoints
- [ ] Production monitoring dashboards
- [ ] Alerting system configuration
- [ ] Log aggregation e analysis

## ✅ Criteri di Completamento

### Testing Coverage
- ✅ >90% code coverage backend
- ✅ >85% code coverage frontend
- ✅ All critical paths tested
- ✅ Performance benchmarks established

### Deployment Readiness
- ✅ Production deployment automated
- ✅ Zero-downtime deployment capability
- ✅ Rollback procedures verified
- ✅ Backup systems operational

### Operational Excellence
- ✅ Monitoring e alerting active
- ✅ Documentation complete
- ✅ Team training completed
- ✅ Support procedures defined

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: DevOps & QA Team* 