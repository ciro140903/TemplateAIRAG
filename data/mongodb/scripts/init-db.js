// Script di inizializzazione MongoDB per il Portale Aziendale

// Selezione database
db = db.getSiblingDB('portal');

print('🚀 Inizializzazione database Portale Aziendale...');

// =============================================
// CREAZIONE COLLEZIONI E INDICI
// =============================================

// Users collection
db.createCollection('users');
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "role": 1 });
db.users.createIndex({ "created_at": -1 });
db.users.createIndex({ "is_active": 1 });

// Chat sessions collection
db.createCollection('chat_sessions');
db.chat_sessions.createIndex({ "user_id": 1 });
db.chat_sessions.createIndex({ "created_at": -1 });
db.chat_sessions.createIndex({ "title": "text" });

// Chat messages collection
db.createCollection('chat_messages');
db.chat_messages.createIndex({ "session_id": 1, "created_at": 1 });
db.chat_messages.createIndex({ "user_id": 1 });
db.chat_messages.createIndex({ "message_type": 1 });

// Documents collection
db.createCollection('documents');
db.documents.createIndex({ "filename": 1 });
db.documents.createIndex({ "user_id": 1 });
db.documents.createIndex({ "file_type": 1 });
db.documents.createIndex({ "upload_date": -1 });
db.documents.createIndex({ "indexed": 1 });
db.documents.createIndex({ "title": "text", "content": "text" });

// Document chunks collection (per RAG)
db.createCollection('document_chunks');
db.document_chunks.createIndex({ "document_id": 1 });
db.document_chunks.createIndex({ "chunk_index": 1 });
db.document_chunks.createIndex({ "vector_id": 1 }, { unique: true });

// Indexing jobs collection
db.createCollection('indexing_jobs');
db.indexing_jobs.createIndex({ "status": 1 });
db.indexing_jobs.createIndex({ "created_at": -1 });
db.indexing_jobs.createIndex({ "document_id": 1 });
db.indexing_jobs.createIndex({ "user_id": 1 });

// System configuration collection
db.createCollection('system_config');
db.system_config.createIndex({ "key": 1 }, { unique: true });

// Audit logs collection
db.createCollection('audit_logs');
db.audit_logs.createIndex({ "user_id": 1 });
db.audit_logs.createIndex({ "action": 1 });
db.audit_logs.createIndex({ "timestamp": -1 });
db.audit_logs.createIndex({ "resource_type": 1 });

// API keys collection (crittografate)
db.createCollection('api_keys');
db.api_keys.createIndex({ "key_name": 1 }, { unique: true });
db.api_keys.createIndex({ "service": 1 });
db.api_keys.createIndex({ "is_active": 1 });

// User sessions collection (per JWT blacklist e gestione sessioni)
db.createCollection('user_sessions');
db.user_sessions.createIndex({ "user_id": 1 });
db.user_sessions.createIndex({ "token_id": 1 }, { unique: true });
db.user_sessions.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });

// =============================================
// DATI INIZIALI
// =============================================

// Utente amministratore di default
const adminUser = {
    "_id": ObjectId(),
    "username": "admin",
    "email": "admin@portal.local",
    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXiBUXK3YUBm", // password: admin123
    "first_name": "Amministratore",
    "last_name": "Sistema",
    "role": "super_admin",
    "is_active": true,
    "is_verified": true,
    "created_at": new Date(),
    "updated_at": new Date(),
    "settings": {
        "theme": "light",
        "language": "it",
        "notifications": true
    },
    "mfa": {
        "enabled": false,
        "secret": null,
        "backup_codes": []
    }
};

db.users.insertOne(adminUser);

// Configurazioni di sistema di default
const systemConfigs = [
    {
        "key": "app_name",
        "value": "Portale Aziendale",
        "type": "string",
        "description": "Nome dell'applicazione"
    },
    {
        "key": "app_version",
        "value": "1.0.0",
        "type": "string",
        "description": "Versione dell'applicazione"
    },
    {
        "key": "max_file_size",
        "value": 104857600,
        "type": "number",
        "description": "Dimensione massima file in bytes (100MB)"
    },
    {
        "key": "allowed_file_types",
        "value": ["pdf", "docx", "xlsx", "txt", "html", "eml"],
        "type": "array",
        "description": "Tipi di file consentiti per l'upload"
    },
    {
        "key": "ai_model_temperature",
        "value": 0.7,
        "type": "number",
        "description": "Temperatura del modello AI (0.0-1.0)"
    },
    {
        "key": "max_tokens_response",
        "value": 2000,
        "type": "number",
        "description": "Numero massimo di token per risposta AI"
    },
    {
        "key": "rag_top_k",
        "value": 5,
        "type": "number",
        "description": "Numero di documenti da recuperare per RAG"
    },
    {
        "key": "embedding_model",
        "value": "text-embedding-3-large",
        "type": "string",
        "description": "Modello per gli embedding"
    },
    {
        "key": "chat_history_limit",
        "value": 50,
        "type": "number",
        "description": "Numero massimo di messaggi nella cronologia chat"
    },
    {
        "key": "registration_enabled",
        "value": false,
        "type": "boolean",
        "description": "Abilita registrazione nuovi utenti"
    }
];

db.system_config.insertMany(systemConfigs);

// Log di sistema per l'inizializzazione
db.audit_logs.insertOne({
    "user_id": adminUser._id,
    "action": "system_init",
    "resource_type": "system",
    "resource_id": null,
    "details": {
        "message": "Database inizializzato con successo",
        "collections_created": [
            "users", "chat_sessions", "chat_messages", "documents",
            "document_chunks", "indexing_jobs", "system_config",
            "audit_logs", "api_keys", "user_sessions"
        ]
    },
    "timestamp": new Date(),
    "ip_address": "127.0.0.1",
    "user_agent": "MongoDB Init Script"
});

print('✅ Database inizializzato con successo!');
print('👤 Utente admin creato: admin@portal.local / admin123');
print('📊 Collezioni create:', db.getCollectionNames().length);
print('🔧 Configurazioni sistema:', db.system_config.countDocuments());
print('📝 Log di audit:', db.audit_logs.countDocuments()); 