# 🏢 Portale Aziendale con AI e RAG

Un portale aziendale completo con intelligenza artificiale avanzata, sistema RAG (Retrieval-Augmented Generation) e indicizzazione multi-formato dei documenti.

## 🚀 Caratteristiche Principali

- **🤖 Chat AI Avanzata**: Conversazioni intelligenti con Azure OpenAI GPT-4
- **📚 Sistema RAG**: Ricerca e generazione aumentata da recupero nei documenti
- **📄 Indicizzazione Multi-formato**: Supporto per PDF, DOCX, XLSX, TXT, HTML, EML
- **👥 Gestione Utenti**: Sistema completo con ruoli e permessi
- **🔐 Sicurezza MFA**: Autenticazione a due fattori con TOTP
- **📊 Monitoring Avanzato**: Grafana + Loki + Promtail
- **🔧 Pannello Admin**: Interfaccia completa di amministrazione
- **🌐 Proxy Manager**: Nginx Proxy Manager integrato

## 🛠️ Stack Tecnologico

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **Microsoft Fluent UI** per l'interfaccia
- **Zustand** per lo state management
- **React Query** per il data fetching

### Backend
- **Python** + **FastAPI** + **Pydantic**
- **MongoDB** per i dati applicativi
- **Qdrant** per i vettori (embeddings)
- **Redis** per la cache e sessioni

### AI & ML
- **Azure OpenAI** (GPT-4 + text-embedding-3-large)
- **Qdrant Vector Database** per la ricerca semantica
- **Chunking intelligente** dei documenti

### Infrastructure
- **Docker** + **Docker Compose**
- **Nginx Proxy Manager**
- **Grafana + Loki + Promtail** monitoring stack

## 📋 Prerequisiti

- **Docker Desktop** (versione recente con Docker Compose V2)
- **Git** per il controllo versione
- **Credenziali Azure OpenAI** (endpoint + API key)
- **Windows 10/11** (attualmente ottimizzato per Windows)

## 🚀 Avvio Rapido

### 1. Clona il Repository
```bash
git clone <repository-url>
cd Progetto1
```

### 2. Configura le Variabili d'Ambiente
```bash
# Copia il file di esempio
copy .env.example .env

# Modifica .env con le tue credenziali Azure OpenAI
# AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE.openai.azure.com/
# AZURE_OPENAI_KEY=YOUR_API_KEY
```

### 3. Avvia il Sistema
```bash
# Esegui lo script di avvio
scripts\start.bat

# Oppure manualmente
docker compose up -d
```

### 4. Verifica l'Installazione
```bash
# Controlla lo stato dei servizi
scripts\status.bat

# Oppure manualmente
docker compose ps
```

## 🌐 Accesso ai Servizi

| Servizio | URL | Credenziali Default |
|----------|-----|-------------------|
| **Grafana** | http://localhost:3000 | admin / portal_grafana_2024 |
| **Nginx Proxy Manager** | http://localhost:81 | admin@example.com / changeme |
| **MongoDB** | localhost:27017 | admin / portal_mongo_2024 |
| **Qdrant** | http://localhost:6333 | - |
| **Redis** | localhost:6379 | Password: portal_redis_2024 |
| **Loki** | http://localhost:3100 | - |

## 📁 Struttura del Progetto

```
Progetto1/
├── 📁 backend/                 # Backend Python FastAPI
├── 📁 frontend/                # Frontend React TypeScript  
├── 📁 fasi/                    # Documentazione fasi sviluppo
├── 📁 data/                    # Dati persistenti database
│   ├── mongodb/                # Dati MongoDB + script init
│   ├── qdrant/                 # Dati Qdrant vector database
│   └── redis/                  # Dati Redis cache
├── 📁 monitoring/              # Configurazioni monitoring
│   ├── grafana/                # Dashboard e configurazioni
│   ├── loki/                   # Configurazione Loki
│   └── promtail/               # Configurazione Promtail
├── 📁 nginx/                   # Dati Nginx Proxy Manager
├── 📁 logs/                    # Log dell'applicazione
├── 📁 uploads/                 # File caricati dagli utenti
├── 📁 scripts/                 # Script di utility
│   ├── start.bat               # Avvio sistema
│   ├── stop.bat                # Arresto sistema
│   ├── status.bat              # Stato sistema
│   └── backup.bat              # Backup dati
├── docker-compose.yml          # Configurazione Docker
├── .env                        # Variabili d'ambiente
└── README.md                   # Questo file
```

## 🔧 Script di Utility

### Gestione Sistema
```bash
# Avvio completo del sistema
scripts\start.bat

# Arresto sistema
scripts\stop.bat

# Verifica stato e salute servizi
scripts\status.bat

# Backup completo dei dati
scripts\backup.bat
```

### Gestione Docker
```bash
# Vedi tutti i container
docker compose ps

# Log di un servizio specifico
docker compose logs -f mongodb

# Restart di un servizio
docker compose restart qdrant

# Arresto completo con rimozione container
docker compose down

# Arresto con rimozione volumi (ATTENZIONE: cancella i dati!)
docker compose down -v
```

## 📊 Monitoring e Logs

### Grafana Dashboards
- **Sistema**: Metriche infrastructure e performance
- **Applicazione**: Metriche business e utilizzo
- **AI & RAG**: Metriche specifiche per le funzionalità AI

### Log Aggregation
- **Loki**: Centralizzazione log da tutti i servizi
- **Promtail**: Raccolta automatica log container
- **Grafana**: Visualizzazione e query sui log

## 🔐 Sicurezza

### Credenziali Default (DA CAMBIARE IN PRODUZIONE!)
- **Database MongoDB**: admin / portal_mongo_2024
- **Redis**: portal_redis_2024
- **Grafana**: admin / portal_grafana_2024
- **Admin Portal**: admin@portal.local / admin123

### Best Practices
- ✅ Cambia tutte le password di default
- ✅ Configura SSL/TLS per la produzione
- ✅ Abilita MFA per gli account admin
- ✅ Rivedi regolarmente i log di audit
- ✅ Mantieni aggiornate le immagini Docker

## 🚧 Stato Sviluppo

### ✅ Completato - FASE 01: Setup Infrastrutturale
- [x] Docker Compose configurazione completa
- [x] Database (MongoDB, Qdrant, Redis) setup
- [x] Monitoring stack (Grafana, Loki, Promtail)
- [x] Nginx Proxy Manager
- [x] Script di utility e automazione
- [x] Inizializzazione database con dati base

### 🔄 In Corso - FASE 02: Backend Core
- [ ] Struttura FastAPI base
- [ ] Modelli Pydantic per MongoDB
- [ ] Sistema autenticazione JWT + MFA
- [ ] Integrazione Azure OpenAI APIs
- [ ] Logging strutturato
- [ ] API documentation

### 📋 Prossime Fasi
- **FASE 03**: Frontend React base
- **FASE 04**: Sistema chat AI
- **FASE 05**: Sistema RAG avanzato
- **FASE 06**: Pannello amministrativo
- **FASE 07**: Sistema indicizzazione
- **FASE 08**: Sicurezza e MFA
- **FASE 09**: Monitoring avanzato
- **FASE 10**: Testing e deployment

## 🐛 Troubleshooting

### Problemi Comuni

**Docker non si avvia**
```bash
# Verifica che Docker Desktop sia in esecuzione
docker version

# Riavvia Docker Desktop se necessario
```

**Errori di connessione database**
```bash
# Verifica lo stato dei database
scripts\status.bat

# Controlla i log
docker compose logs mongodb
docker compose logs qdrant
docker compose logs redis
```

**Problemi di permessi**
```bash
# Su Windows normalmente non ci sono problemi di permessi
# Se necessario, esegui come amministratore
```

**Out of memory**
```bash
# Aumenta la memoria allocata a Docker Desktop
# Settings > Resources > Memory (consigliato: 4GB+)
```

### Log Locations
- **Application logs**: `./logs/`
- **Container logs**: `docker compose logs [service]`
- **MongoDB logs**: Accessibili via Grafana o `docker compose exec mongodb`
- **System logs**: Dashboard Grafana "Infrastructure"

## 📚 Documentazione Tecnica

La documentazione completa dello sviluppo è disponibile nella cartella `fasi/`:

- **[00-INDICE-GENERALE.md](fasi/00-INDICE-GENERALE.md)**: Overview completo del progetto
- **[01-setup-infrastrutturale.md](fasi/01-setup-infrastrutturale.md)**: Dettagli fase attuale
- **[architettura-sistema.md](fasi/architettura-sistema.md)**: Architettura tecnica completa
- **[dipendenze-fasi.md](fasi/dipendenze-fasi.md)**: Analisi dipendenze e timeline
- **[considerazioni-tecniche.md](fasi/considerazioni-tecniche.md)**: Decisioni architetturali
- **[checklist-qualita.md](fasi/checklist-qualita.md)**: Criteri di qualità e testing

## 🤝 Contributi

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/nome-feature`)
3. Commit delle modifiche (`git commit -am 'Aggiunge nome-feature'`)
4. Push del branch (`git push origin feature/nome-feature`)
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è licenziato sotto [MIT License](LICENSE).

## 📞 Supporto

Per supporto e domande:
- 📧 Email: [inserire email di supporto]
- 💬 Discord: [inserire link Discord se disponibile]
- 🐛 Issues: [GitHub Issues](repository-url/issues)

---

🚀 **Happy Coding!** Costruiamo insieme il futuro dell'automazione aziendale con AI! 