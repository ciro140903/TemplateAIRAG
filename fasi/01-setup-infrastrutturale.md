# 🏗️ FASE 01: SETUP INFRASTRUTTURALE

## 📋 Panoramica Fase

Configurazione dell'infrastruttura base del progetto con tutti i servizi containerizzati necessari per il funzionamento del portale web aziendale.

## 🎯 Obiettivi

- **Infrastruttura Completa**: Setup di tutti i servizi Docker
- **Networking**: Configurazione rete interna e reverse proxy
- **Monitoring Base**: Configurazione logging e monitoring
- **Database Setup**: Inizializzazione MongoDB e Qdrant
- **Development Environment**: Ambiente di sviluppo funzionante

## ⏱️ Timeline

- **Durata Stimata**: 5-7 giorni
- **Priorità**: ⭐⭐⭐ CRITICA
- **Dipendenze**: Nessuna
- **Blocca**: Tutte le altre fasi

## 🛠️ Task Dettagliati

### 1. Struttura Progetto Base
- [ ] **Creazione struttura cartelle**
  ```
  Progetto1/
  ├── backend/
  ├── frontend/
  ├── docker/
  │   ├── mongodb/
  │   ├── qdrant/
  │   └── nginx/
  ├── monitoring/
  │   ├── grafana/
  │   ├── loki/
  │   └── promtail/
  └── docs/
  ```

- [ ] **File configurazione globali**
  - `.env.example` con tutte le variabili necessarie
  - `.gitignore` appropriato per Python/Node.js
  - `README.md` con istruzioni setup

### 2. Docker Compose Configuration

- [ ] **docker-compose.yml principale**
  - Servizio MongoDB con persistenza
  - Servizio Qdrant con configurazione custom
  - Servizio Nginx Proxy Manager
  - Servizio Grafana + Loki + Promtail
  - Network configuration tra servizi

- [ ] **Docker networks setup**
  ```yaml
  networks:
    app-network:
      driver: bridge
    monitoring-network:
      driver: bridge
  ```

### 3. MongoDB Setup

- [ ] **Configurazione MongoDB**
  - Database inizializzazione script
  - User e ruoli di base
  - Indici per performance
  - Replica set (opzionale per produzione)

- [ ] **Docker MongoDB service**
  ```yaml
  mongodb:
    image: mongo:7.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: portal_db
    volumes:
      - mongodb_data:/data/db
      - ./docker/mongodb/init:/docker-entrypoint-initdb.d
  ```

### 4. Qdrant Configuration

- [ ] **Qdrant setup**
  - Configurazione storage settings
  - API key configuration
  - Collection templates
  - Backup configuration

- [ ] **Docker Qdrant service**
  ```yaml
  qdrant:
    image: qdrant/qdrant:v1.7.0
    environment:
      QDRANT__SERVICE__HTTP_PORT: 6333
      QDRANT__SERVICE__GRPC_PORT: 6334
    volumes:
      - qdrant_data:/qdrant/storage
      - ./docker/qdrant/config:/qdrant/config
  ```

### 5. Nginx Proxy Manager

- [ ] **NPM Configuration**
  - Setup iniziale con admin user
  - SSL certificates (Let's Encrypt)
  - Proxy hosts configuration
  - Access lists per sicurezza

- [ ] **Docker NPM service**
  ```yaml
  nginx-proxy-manager:
    image: jc21/nginx-proxy-manager:latest
    environment:
      DB_MYSQL_HOST: npm-db
      DB_MYSQL_NAME: npm
      DB_MYSQL_USER: npm
      DB_MYSQL_PASSWORD: ${NPM_DB_PASSWORD}
    volumes:
      - npm_data:/data
      - npm_ssl:/etc/letsencrypt
  ```

### 6. Monitoring Stack (Grafana + Loki)

- [ ] **Grafana Setup**
  - Dashboard configurazioni di base
  - Data sources (Loki, Prometheus)
  - User provisioning
  - Plugin installations

- [ ] **Loki Configuration**
  - Log retention policies
  - Storage configuration
  - Indexing strategy
  - Query optimization

- [ ] **Promtail Setup**
  - Log collection rules
  - Parsing configurations
  - Label extraction
  - Multi-line log handling

### 7. Development Environment

- [ ] **Environment Variables**
  ```bash
  # Database
  MONGO_PASSWORD=secure_password
  MONGO_DATABASE=portal_db
  
  # Qdrant
  QDRANT_API_KEY=qdrant_api_key
  QDRANT_HOST=qdrant
  
  # Azure AI
  AZURE_OPENAI_ENDPOINT=your_endpoint
  AZURE_OPENAI_API_KEY=your_key
  
  # Security
  JWT_SECRET=your_jwt_secret
  ENCRYPTION_KEY=your_encryption_key
  ```

- [ ] **Development Scripts**
  - `scripts/dev-start.sh` - Avvio ambiente sviluppo
  - `scripts/dev-stop.sh` - Stop e cleanup
  - `scripts/dev-reset.sh` - Reset completo database
  - `scripts/backup.sh` - Backup automatico dati

### 8. Health Checks e Monitoring

- [ ] **Health Check Endpoints**
  - MongoDB connection check
  - Qdrant service check
  - Network connectivity tests
  - Disk space monitoring

- [ ] **Basic Alerting**
  - Service down alerts
  - Resource usage alerts
  - Error rate monitoring
  - Response time tracking

## 📦 Deliverable

### File di Configurazione
- [ ] `docker-compose.yml` completo e testato
- [ ] File `.env.example` con tutte le variabili
- [ ] Script di inizializzazione database
- [ ] Configurazioni Nginx, Grafana, Loki

### Documentazione
- [ ] `README.md` con istruzioni setup
- [ ] Guida troubleshooting comune
- [ ] Documentazione architettura servizi
- [ ] Procedure backup e restore

### Testing
- [ ] Verifica startup di tutti i servizi
- [ ] Test connectivity tra servizi
- [ ] Validazione configurazioni security
- [ ] Performance test preliminari

## ✅ Criteri di Completamento

### Funzionali
- ✅ Tutti i servizi Docker sono avviabili con `docker-compose up`
- ✅ MongoDB è accessibile e configurato correttamente
- ✅ Qdrant risponde alle API calls di base
- ✅ Grafana è accessibile con dashboard di base
- ✅ Nginx Proxy Manager è configurato e funzionante

### Non-Funzionali
- ✅ Startup time < 2 minuti per tutti i servizi
- ✅ Memory usage < 4GB per l'intero stack
- ✅ Persistent data correttamente mappata
- ✅ Network segmentation configurata

### Documentazione
- ✅ Tutti i file di configurazione sono documentati
- ✅ Procedure di troubleshooting sono testate
- ✅ Script di automazione funzionano correttamente

## 🚨 Rischi e Mitigazioni

### Rischi Tecnici
- **Conflitti Porte**: Audit porte in uso e mapping dinamico
- **Performance Docker**: Resource limits e monitoring
- **Compatibility OS**: Test su Windows/Linux/macOS

### Rischi di Progetto  
- **Complessità Setup**: Documentazione step-by-step dettagliata
- **Dipendenze Esterne**: Fallback per servizi esterni
- **Time Estimation**: Buffer 30% per troubleshooting

## 🔗 Dipendenze Esterne

- **Docker & Docker Compose**: Versione 20.10+
- **Available Ports**: 80, 443, 3000, 6333, 3100, 27017
- **System Resources**: 8GB RAM minimo, 50GB storage
- **Network Access**: Per download images e certificati SSL

## 📄 File di Supporto

- **Configuration Templates**: `./templates/`
- **Scripts Automazione**: `./scripts/`
- **Health Check Tests**: `./tests/infrastructure/`
- **Backup Procedures**: `./docs/backup.md`

---

## 🎯 Prossimi Passi

Al completamento di questa fase:
1. **Validation Meeting**: Review setup con team
2. **Performance Baseline**: Metriche iniziali sistema
3. **Security Audit**: Controllo configurazioni sicurezza
4. **Avvio Fase 02 e 03**: Sviluppo parallelo backend/frontend

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: Infrastructure Team* 