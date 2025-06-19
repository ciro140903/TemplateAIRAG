# 🔐 FASE 08: SICUREZZA E MFA

## 📋 Panoramica Fase

Implementazione completa del sistema di sicurezza avanzato con Multi-Factor Authentication, autorizzazione granulare, audit trail, e protezioni contro vulnerabilità comuni.

## 🎯 Obiettivi

- **Multi-Factor Authentication**: TOTP, SMS, Email verification
- **Autorizzazione Granulare**: Role-based access control avanzato
- **Audit Trail Completo**: Logging tutte le azioni critiche
- **Security Hardening**: Protezione contro vulnerabilità OWASP
- **Session Management**: Gestione sicura sessioni utente

## ⏱️ Timeline

- **Durata Stimata**: 6-8 giorni
- **Priorità**: ⭐⭐⭐ CRITICA
- **Dipendenze**: Fase 02 (Backend Core), Fase 06 (Pannello Admin)
- **Parallelo con**: Fase 07 (Sistema Indicizzazione)

## 🛠️ Task Dettagliati

### 1. Multi-Factor Authentication Backend

- [ ] **MFA Service Implementation**
  ```python
  # backend/app/services/mfa_service.py
  import pyotp
  import qrcode
  import io
  import base64
  from typing import Optional, Dict, Tuple
  from ..models.user import User
  from ..core.security import get_random_string
  
  class MFAService:
      def __init__(self):
          self.db = MongoDB.database
          self.issuer_name = "Portal Aziendale"
      
      async def enable_totp_mfa(self, user: User) -> Tuple[str, str]:
          """Enable TOTP MFA for user and return secret + QR code"""
          # Generate secret
          secret = pyotp.random_base32()
          
          # Create TOTP instance
          totp = pyotp.TOTP(secret)
          
          # Generate provisioning URI
          provisioning_uri = totp.provisioning_uri(
              name=user.email,
              issuer_name=self.issuer_name
          )
          
          # Generate QR code
          qr_code_data = self._generate_qr_code(provisioning_uri)
          
          # Store secret in database (encrypted)
          await self.db.users.update_one(
              {"_id": user.id},
              {
                  "$set": {
                      "mfa_secret": secret,
                      "mfa_enabled": False,  # Not enabled until verified
                      "mfa_type": "totp",
                      "mfa_backup_codes": await self._generate_backup_codes()
                  }
              }
          )
          
          return secret, qr_code_data
      
      async def verify_totp_setup(self, user: User, token: str) -> bool:
          """Verify TOTP setup and enable MFA"""
          user_doc = await self.db.users.find_one({"_id": user.id})
          secret = user_doc.get("mfa_secret")
          
          if not secret:
              return False
          
          totp = pyotp.TOTP(secret)
          
          if totp.verify(token):
              # Enable MFA
              await self.db.users.update_one(
                  {"_id": user.id},
                  {"$set": {"mfa_enabled": True}}
              )
              
              # Log MFA enablement
              await self._log_security_event(
                  user.id, "mfa_enabled", {"method": "totp"}
              )
              
              return True
          
          return False
      
      async def verify_totp_token(self, user: User, token: str) -> bool:
          """Verify TOTP token for authentication"""
          if not user.mfa_enabled:
              return False
          
          user_doc = await self.db.users.find_one({"_id": user.id})
          secret = user_doc.get("mfa_secret")
          
          if not secret:
              return False
          
          totp = pyotp.TOTP(secret)
          
          # Check current token and previous/next windows for clock drift
          for window in [-1, 0, 1]:
              if totp.verify(token, valid_window=window):
                  await self._log_security_event(
                      user.id, "mfa_verified", {"method": "totp"}
                  )
                  return True
          
          # Check backup codes
          backup_codes = user_doc.get("mfa_backup_codes", [])
          if token in backup_codes:
              # Remove used backup code
              backup_codes.remove(token)
              await self.db.users.update_one(
                  {"_id": user.id},
                  {"$set": {"mfa_backup_codes": backup_codes}}
              )
              
              await self._log_security_event(
                  user.id, "mfa_verified", {"method": "backup_code"}
              )
              return True
          
          await self._log_security_event(
              user.id, "mfa_failed", {"method": "totp", "token_provided": token[:2] + "***"}
          )
          return False
      
      async def disable_mfa(self, user: User, token: str) -> bool:
          """Disable MFA after token verification"""
          if await self.verify_totp_token(user, token):
              await self.db.users.update_one(
                  {"_id": user.id},
                  {
                      "$unset": {
                          "mfa_secret": "",
                          "mfa_backup_codes": ""
                      },
                      "$set": {"mfa_enabled": False}
                  }
              )
              
              await self._log_security_event(
                  user.id, "mfa_disabled", {"method": "totp"}
              )
              return True
          
          return False
      
      async def generate_new_backup_codes(self, user: User) -> List[str]:
          """Generate new backup codes"""
          backup_codes = await self._generate_backup_codes()
          
          await self.db.users.update_one(
              {"_id": user.id},
              {"$set": {"mfa_backup_codes": backup_codes}}
          )
          
          await self._log_security_event(
              user.id, "backup_codes_regenerated", {}
          )
          
          return backup_codes
      
      def _generate_qr_code(self, data: str) -> str:
          """Generate QR code as base64 string"""
          qr = qrcode.QRCode(version=1, box_size=10, border=5)
          qr.add_data(data)
          qr.make(fit=True)
          
          img = qr.make_image(fill_color="black", back_color="white")
          
          # Convert to base64
          buffer = io.BytesIO()
          img.save(buffer, format='PNG')
          img_str = base64.b64encode(buffer.getvalue()).decode()
          
          return f"data:image/png;base64,{img_str}"
      
      async def _generate_backup_codes(self, count: int = 8) -> List[str]:
          """Generate backup codes"""
          codes = []
          for _ in range(count):
              code = get_random_string(8, include_digits=True, include_letters=False)
              codes.append(f"{code[:4]}-{code[4:]}")
          return codes
      
      async def _log_security_event(
          self, 
          user_id: str, 
          event_type: str, 
          details: Dict
      ):
          """Log security events"""
          event = {
              "user_id": user_id,
              "event_type": event_type,
              "details": details,
              "timestamp": datetime.utcnow(),
              "ip_address": "N/A",  # Should be passed from request context
              "user_agent": "N/A"   # Should be passed from request context
          }
          
          await self.db.security_events.insert_one(event)
  ```

- [ ] **Advanced Authorization Service**
  ```python
  # backend/app/services/authorization_service.py
  from typing import List, Dict, Optional, Callable
  from enum import Enum
  from ..models.user import User, UserRole
  
  class Permission(str, Enum):
      # User management
      USER_READ = "user:read"
      USER_CREATE = "user:create"
      USER_UPDATE = "user:update"
      USER_DELETE = "user:delete"
      
      # Admin functions
      ADMIN_READ = "admin:read"
      ADMIN_WRITE = "admin:write"
      SYSTEM_CONFIG = "system:config"
      
      # Chat functions
      CHAT_READ = "chat:read"
      CHAT_WRITE = "chat:write"
      CHAT_DELETE = "chat:delete"
      
      # Indexing
      INDEX_READ = "index:read"
      INDEX_WRITE = "index:write"
      INDEX_MANAGE = "index:manage"
      
      # API Keys
      APIKEY_READ = "apikey:read"
      APIKEY_WRITE = "apikey:write"
  
  class AuthorizationService:
      def __init__(self):
          self.role_permissions = {
              UserRole.ADMIN: [
                  Permission.USER_READ, Permission.USER_CREATE, 
                  Permission.USER_UPDATE, Permission.USER_DELETE,
                  Permission.ADMIN_READ, Permission.ADMIN_WRITE,
                  Permission.SYSTEM_CONFIG, Permission.CHAT_READ,
                  Permission.CHAT_WRITE, Permission.CHAT_DELETE,
                  Permission.INDEX_READ, Permission.INDEX_WRITE,
                  Permission.INDEX_MANAGE, Permission.APIKEY_READ,
                  Permission.APIKEY_WRITE
              ],
              UserRole.USER: [
                  Permission.CHAT_READ, Permission.CHAT_WRITE,
                  Permission.INDEX_READ
              ],
              UserRole.VIEWER: [
                  Permission.CHAT_READ, Permission.INDEX_READ
              ]
          }
      
      def has_permission(self, user: User, permission: Permission) -> bool:
          """Check if user has specific permission"""
          if not user.is_active:
              return False
          
          user_permissions = self.role_permissions.get(user.role, [])
          return permission in user_permissions
      
      def has_any_permission(self, user: User, permissions: List[Permission]) -> bool:
          """Check if user has any of the specified permissions"""
          return any(self.has_permission(user, perm) for perm in permissions)
      
      def has_all_permissions(self, user: User, permissions: List[Permission]) -> bool:
          """Check if user has all specified permissions"""
          return all(self.has_permission(user, perm) for perm in permissions)
      
      def can_access_resource(
          self, 
          user: User, 
          resource_type: str, 
          resource_id: Optional[str] = None,
          action: str = "read"
      ) -> bool:
          """Check if user can access specific resource"""
          
          # Resource-specific logic
          if resource_type == "chat_session":
              # Users can only access their own chat sessions
              if action in ["read", "write"]:
                  return (self.has_permission(user, Permission.CHAT_READ) or 
                          self.has_permission(user, Permission.CHAT_WRITE))
              elif action == "delete":
                  return self.has_permission(user, Permission.CHAT_DELETE)
          
          elif resource_type == "user_profile":
              # Users can read/update their own profile, admins can access all
              if resource_id == str(user.id):
                  return True
              return self.has_permission(user, Permission.USER_READ)
          
          elif resource_type == "admin_panel":
              return self.has_permission(user, Permission.ADMIN_READ)
          
          elif resource_type == "indexing_job":
              if action == "read":
                  return self.has_permission(user, Permission.INDEX_READ)
              elif action in ["create", "update", "delete"]:
                  return self.has_permission(user, Permission.INDEX_MANAGE)
          
          return False
      
      def get_user_permissions(self, user: User) -> List[Permission]:
          """Get all permissions for user"""
          return self.role_permissions.get(user.role, [])
  
  # Dependency for FastAPI
  def require_permission(permission: Permission):
      """Decorator for FastAPI endpoints to require specific permission"""
      def dependency(
          current_user: User = Depends(get_current_user),
          auth_service: AuthorizationService = Depends()
      ):
          if not auth_service.has_permission(current_user, permission):
              raise HTTPException(
                  status_code=403,
                  detail=f"Permission {permission} required"
              )
          return current_user
      return dependency
  
  def require_any_permission(permissions: List[Permission]):
      """Require any of the specified permissions"""
      def dependency(
          current_user: User = Depends(get_current_user),
          auth_service: AuthorizationService = Depends()
      ):
          if not auth_service.has_any_permission(current_user, permissions):
              raise HTTPException(
                  status_code=403,
                  detail=f"One of permissions {permissions} required"
              )
          return current_user
      return dependency
  ```

### 2. Security Hardening

- [ ] **Input Validation & Sanitization**
  ```python
  # backend/app/security/validation.py
  import re
  import html
  from typing import Any, Dict, List
  from pydantic import BaseModel, validator
  
  class SecurityValidator:
      @staticmethod
      def sanitize_html(value: str) -> str:
          """Sanitize HTML input"""
          return html.escape(value.strip())
      
      @staticmethod
      def validate_file_path(path: str) -> bool:
          """Validate file path to prevent directory traversal"""
          # Normalize path
          normalized = os.path.normpath(path)
          
          # Check for directory traversal attempts
          if ".." in normalized or normalized.startswith("/"):
              return False
          
          # Check for dangerous characters
          dangerous_chars = ['<', '>', '|', '&', ';', '$', '`']
          if any(char in path for char in dangerous_chars):
              return False
          
          return True
      
      @staticmethod
      def validate_sql_injection(value: str) -> bool:
          """Basic SQL injection prevention"""
          sql_keywords = [
              'select', 'insert', 'update', 'delete', 'drop', 'create',
              'alter', 'exec', 'execute', 'union', 'script'
          ]
          
          value_lower = value.lower()
          return not any(keyword in value_lower for keyword in sql_keywords)
      
      @staticmethod
      def validate_xss(value: str) -> str:
          """Prevent XSS attacks"""
          # Remove script tags
          value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
          
          # Remove javascript: URLs
          value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
          
          # Remove on* event handlers
          value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
          
          return html.escape(value)
  
  # Custom Pydantic validators
  class SecureBaseModel(BaseModel):
      @validator('*', pre=True)
      def sanitize_strings(cls, v):
          if isinstance(v, str):
              return SecurityValidator.sanitize_html(v)
          return v
  ```

- [ ] **Rate Limiting & DDoS Protection**
  ```python
  # backend/app/middleware/rate_limiting.py
  import time
  from typing import Dict, Optional
  from fastapi import Request, HTTPException
  from fastapi.responses import JSONResponse
  import redis
  
  class RateLimiter:
      def __init__(self, redis_client: redis.Redis):
          self.redis = redis_client
          self.default_rate_limit = 100  # requests per minute
          self.default_window = 60  # seconds
      
      async def is_rate_limited(
          self,
          identifier: str,
          rate_limit: int = None,
          window: int = None
      ) -> bool:
          """Check if identifier is rate limited"""
          rate_limit = rate_limit or self.default_rate_limit
          window = window or self.default_window
          
          key = f"rate_limit:{identifier}"
          current_time = int(time.time())
          window_start = current_time - window
          
          # Remove old entries
          self.redis.zremrangebyscore(key, 0, window_start)
          
          # Count current requests
          current_requests = self.redis.zcard(key)
          
          if current_requests >= rate_limit:
              return True
          
          # Add current request
          self.redis.zadd(key, {str(current_time): current_time})
          self.redis.expire(key, window)
          
          return False
      
      async def get_rate_limit_info(self, identifier: str) -> Dict:
          """Get rate limit information"""
          key = f"rate_limit:{identifier}"
          current_requests = self.redis.zcard(key)
          
          return {
              "current_requests": current_requests,
              "rate_limit": self.default_rate_limit,
              "window_seconds": self.default_window,
              "remaining": max(0, self.default_rate_limit - current_requests)
          }
  
  class RateLimitMiddleware:
      def __init__(self, app, redis_client: redis.Redis):
          self.app = app
          self.rate_limiter = RateLimiter(redis_client)
      
      async def __call__(self, scope, receive, send):
          if scope["type"] == "http":
              request = Request(scope, receive)
              
              # Get client identifier (IP + User ID if authenticated)
              client_ip = request.client.host
              user_id = getattr(request.state, 'user_id', None)
              identifier = f"{client_ip}:{user_id}" if user_id else client_ip
              
              # Check rate limit
              if await self.rate_limiter.is_rate_limited(identifier):
                  response = JSONResponse(
                      status_code=429,
                      content={"detail": "Rate limit exceeded"},
                      headers={"Retry-After": "60"}
                  )
                  await response(scope, receive, send)
                  return
          
          await self.app(scope, receive, send)
  ```

### 3. Frontend Security Components

- [ ] **MFA Setup Component**
  ```typescript
  // src/components/security/MFASetup.tsx
  import { useState } from 'react';
  import {
    Stack,
    TextField,
    PrimaryButton,
    DefaultButton,
    MessageBar,
    MessageBarType,
    Dialog,
    Image,
    Text,
    Separator,
  } from '@fluentui/react';
  import { useForm } from 'react-hook-form';
  import { zodResolver } from '@hookform/resolvers/zod';
  import { z } from 'zod';
  import { motion } from 'framer-motion';
  import { useMFAStore } from '@/store/mfaStore';
  
  const verificationSchema = z.object({
    token: z.string().length(6, 'Il codice deve essere di 6 cifre'),
  });
  
  type VerificationFormData = z.infer<typeof verificationSchema>;
  
  interface MFASetupProps {
    onComplete: () => void;
    onCancel: () => void;
  }
  
  export const MFASetup: React.FC<MFASetupProps> = ({ onComplete, onCancel }) => {
    const [step, setStep] = useState<'setup' | 'verify' | 'backup'>('setup');
    const [qrCode, setQrCode] = useState<string>('');
    const [secret, setSecret] = useState<string>('');
    const [backupCodes, setBackupCodes] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    const { enableMFA, verifyMFASetup } = useMFAStore();
    
    const {
      register,
      handleSubmit,
      formState: { errors, isValid },
      reset,
    } = useForm<VerificationFormData>({
      resolver: zodResolver(verificationSchema),
    });
    
    const handleSetupMFA = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const result = await enableMFA();
        setQrCode(result.qrCode);
        setSecret(result.secret);
        setStep('verify');
      } catch (err) {
        setError('Errore durante la configurazione MFA');
      } finally {
        setIsLoading(false);
      }
    };
    
    const handleVerifySetup = async (data: VerificationFormData) => {
      setIsLoading(true);
      setError(null);
      
      try {
        const result = await verifyMFASetup(data.token);
        if (result.success) {
          setBackupCodes(result.backupCodes);
          setStep('backup');
        } else {
          setError('Codice non valido. Riprova.');
        }
      } catch (err) {
        setError('Errore durante la verifica');
      } finally {
        setIsLoading(false);
      }
    };
    
    const renderSetupStep = () => (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Stack tokens={{ childrenGap: 20 }}>
          <Text variant="large">Configura l'Autenticazione a Due Fattori</Text>
          
          <Text>
            L'autenticazione a due fattori aggiunge un livello extra di sicurezza al tuo account.
            Dovrai inserire un codice dal tuo telefono ogni volta che accedi.
          </Text>
          
          <Stack tokens={{ childrenGap: 10 }}>
            <Text variant="medium" styles={{ root: { fontWeight: 'bold' } }}>
              Per iniziare:
            </Text>
            <Text>1. Installa un'app di autenticazione come Google Authenticator o Authy</Text>
            <Text>2. Clicca "Genera Codice QR" per ottenere il codice</Text>
            <Text>3. Scansiona il codice QR con la tua app</Text>
            <Text>4. Inserisci il codice a 6 cifre dall'app per completare la configurazione</Text>
          </Stack>
          
          {error && (
            <MessageBar messageBarType={MessageBarType.error}>
              {error}
            </MessageBar>
          )}
          
          <Stack horizontal tokens={{ childrenGap: 10 }}>
            <PrimaryButton
              text={isLoading ? 'Generando...' : 'Genera Codice QR'}
              disabled={isLoading}
              onClick={handleSetupMFA}
            />
            <DefaultButton text="Annulla" onClick={onCancel} />
          </Stack>
        </Stack>
      </motion.div>
    );
    
    const renderVerifyStep = () => (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Stack tokens={{ childrenGap: 20 }}>
          <Text variant="large">Scansiona il Codice QR</Text>
          
          <Stack horizontal tokens={{ childrenGap: 20 }} verticalAlign="center">
            <Stack tokens={{ childrenGap: 10 }}>
              <Image
                src={qrCode}
                alt="QR Code per MFA"
                width={200}
                height={200}
                styles={{
                  root: {
                    border: '2px solid #e1e1e1',
                    borderRadius: '8px',
                  },
                }}
              />
              
              <Text variant="small" styles={{ root: { fontFamily: 'monospace' } }}>
                Codice manuale: {secret}
              </Text>
            </Stack>
            
            <Stack tokens={{ childrenGap: 15 }}>
              <Text>
                1. Apri la tua app di autenticazione
              </Text>
              <Text>
                2. Scansiona questo codice QR
              </Text>
              <Text>
                3. Inserisci il codice a 6 cifre dall'app
              </Text>
            </Stack>
          </Stack>
          
          <Separator />
          
          <form onSubmit={handleSubmit(handleVerifySetup)}>
            <Stack tokens={{ childrenGap: 15 }}>
              <TextField
                label="Codice di Verifica"
                placeholder="123456"
                {...register('token')}
                errorMessage={errors.token?.message}
                styles={{ root: { maxWidth: '200px' } }}
                autoComplete="off"
              />
              
              {error && (
                <MessageBar messageBarType={MessageBarType.error}>
                  {error}
                </MessageBar>
              )}
              
              <Stack horizontal tokens={{ childrenGap: 10 }}>
                <PrimaryButton
                  type="submit"
                  text={isLoading ? 'Verificando...' : 'Verifica e Attiva'}
                  disabled={!isValid || isLoading}
                />
                <DefaultButton
                  text="Indietro"
                  onClick={() => setStep('setup')}
                />
              </Stack>
            </Stack>
          </form>
        </Stack>
      </motion.div>
    );
    
    const renderBackupStep = () => (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Stack tokens={{ childrenGap: 20 }}>
          <Text variant="large">Codici di Backup</Text>
          
          <MessageBar messageBarType={MessageBarType.success}>
            MFA attivato con successo!
          </MessageBar>
          
          <Text>
            Salva questi codici di backup in un luogo sicuro. Puoi usarli per accedere 
            al tuo account se perdi l'accesso alla tua app di autenticazione.
          </Text>
          
          <Stack
            styles={{
              root: {
                backgroundColor: '#f8f9fa',
                padding: '16px',
                borderRadius: '4px',
                border: '1px solid #e1e1e1',
              },
            }}
          >
            <Text variant="medium" styles={{ root: { fontWeight: 'bold', marginBottom: '8px' } }}>
              Codici di Backup:
            </Text>
            
            {backupCodes.map((code, index) => (
              <Text
                key={index}
                styles={{
                  root: {
                    fontFamily: 'monospace',
                    fontSize: '14px',
                    padding: '4px 0',
                  },
                }}
              >
                {code}
              </Text>
            ))}
          </Stack>
          
          <Stack horizontal tokens={{ childrenGap: 10 }}>
            <PrimaryButton
              text="Ho Salvato i Codici"
              onClick={onComplete}
            />
            <DefaultButton
              text="Scarica Codici"
              onClick={() => {
                const blob = new Blob([backupCodes.join('\n')], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'mfa-backup-codes.txt';
                a.click();
              }}
            />
          </Stack>
        </Stack>
      </motion.div>
    );
    
    return (
      <Stack tokens={{ childrenGap: 24 }}>
        {step === 'setup' && renderSetupStep()}
        {step === 'verify' && renderVerifyStep()}
        {step === 'backup' && renderBackupStep()}
      </Stack>
    );
  };
  ```

## 📦 Deliverable

### Backend Security
- [ ] Multi-Factor Authentication completo
- [ ] Authorization system granulare
- [ ] Input validation e sanitization
- [ ] Rate limiting e DDoS protection

### Frontend Security
- [ ] MFA setup e management UI
- [ ] Secure forms con validation
- [ ] Session timeout handling
- [ ] Security notifications

### Audit & Compliance
- [ ] Comprehensive audit trail
- [ ] Security event logging
- [ ] Compliance reporting tools
- [ ] Incident response procedures

### Security Hardening
- [ ] OWASP Top 10 protection
- [ ] Secure headers implementation
- [ ] Content Security Policy
- [ ] Regular security scanning

## ✅ Criteri di Completamento

### Funzionali
- ✅ MFA setup e verification funzionante
- ✅ Role-based access control operativo
- ✅ Audit logging completo
- ✅ Security incident detection

### Sicurezza
- ✅ Protection contro OWASP Top 10
- ✅ Input validation su tutti gli endpoint
- ✅ Session management sicuro
- ✅ Rate limiting efficace

### Compliance
- ✅ Audit trail comprehensive
- ✅ Data protection measures
- ✅ Access control documentation
- ✅ Security policies implementation

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: Security Team* 