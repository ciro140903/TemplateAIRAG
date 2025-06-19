# 🛠️ FASE 06: PANNELLO AMMINISTRATIVO

## 📋 Panoramica Fase

Sviluppo del pannello amministrativo completo per la gestione di utenti, ruoli, configurazioni di sistema, chiavi API, e monitoraggio delle funzionalità del portale.

## 🎯 Obiettivi

- **Gestione Utenti Completa**: CRUD utenti, ruoli e permessi
- **Configurazioni Sistema**: Settings generali configurabili via UI
- **API Keys Management**: Gestione sicura chiavi esterne
- **Dashboard Analytics**: Metriche utilizzo e performance
- **System Health**: Monitoring stato servizi

## ⏱️ Timeline

- **Durata Stimata**: 8-10 giorni
- **Priorità**: ⭐⭐ ALTA
- **Dipendenze**: Fase 03 (Frontend Base), Fase 02 (Backend Core)
- **Parallelo con**: Fase 07 (Sistema Indicizzazione)

## 🛠️ Task Dettagliati

### 1. Backend Admin APIs

- [ ] **Admin User Management Service**
  ```python
  # backend/app/services/admin_service.py
  from typing import List, Optional, Dict
  from ..models.user import User, UserRole, UserCreate, UserUpdate
  from ..core.security import get_password_hash
  
  class AdminService:
      def __init__(self):
          self.db = MongoDB.database
      
      async def get_users(
          self, 
          skip: int = 0, 
          limit: int = 100,
          role_filter: Optional[UserRole] = None,
          search: Optional[str] = None
      ) -> List[User]:
          """Get paginated users with optional filters"""
          query = {}
          
          if role_filter:
              query["role"] = role_filter
          
          if search:
              query["$or"] = [
                  {"email": {"$regex": search, "$options": "i"}},
                  {"username": {"$regex": search, "$options": "i"}},
                  {"full_name": {"$regex": search, "$options": "i"}}
              ]
          
          cursor = self.db.users.find(query).skip(skip).limit(limit)
          users = []
          async for doc in cursor:
              users.append(User(**doc))
          
          return users
      
      async def create_user(self, user_data: UserCreate) -> User:
          """Create new user (admin only)"""
          # Check if user already exists
          existing = await self.db.users.find_one({
              "$or": [
                  {"email": user_data.email},
                  {"username": user_data.username}
              ]
          })
          
          if existing:
              raise ValueError("User with this email or username already exists")
          
          user = User(
              email=user_data.email,
              username=user_data.username,
              full_name=user_data.full_name,
              hashed_password=get_password_hash(user_data.password),
              role=user_data.role,
              is_active=True,
              is_verified=True  # Admin-created users are pre-verified
          )
          
          result = await self.db.users.insert_one(user.dict(by_alias=True))
          user.id = result.inserted_id
          
          return user
      
      async def update_user(self, user_id: str, user_update: UserUpdate) -> User:
          """Update user information"""
          update_data = user_update.dict(exclude_unset=True)
          
          if "password" in update_data:
              update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
          
          if update_data:
              await self.db.users.update_one(
                  {"_id": ObjectId(user_id)},
                  {"$set": update_data}
              )
          
          updated_user = await self.db.users.find_one({"_id": ObjectId(user_id)})
          return User(**updated_user)
      
      async def delete_user(self, user_id: str) -> bool:
          """Soft delete user"""
          result = await self.db.users.update_one(
              {"_id": ObjectId(user_id)},
              {"$set": {"is_active": False, "deleted_at": datetime.utcnow()}}
          )
          return result.modified_count > 0
      
      async def get_user_stats(self) -> Dict:
          """Get user statistics"""
          total_users = await self.db.users.count_documents({})
          active_users = await self.db.users.count_documents({"is_active": True})
          verified_users = await self.db.users.count_documents({"is_verified": True})
          
          # Role distribution
          role_stats = await self.db.users.aggregate([
              {"$group": {"_id": "$role", "count": {"$sum": 1}}}
          ]).to_list(None)
          
          # Recent registrations (last 30 days)
          thirty_days_ago = datetime.utcnow() - timedelta(days=30)
          recent_registrations = await self.db.users.count_documents({
              "created_at": {"$gte": thirty_days_ago}
          })
          
          return {
              "total_users": total_users,
              "active_users": active_users,
              "verified_users": verified_users,
              "role_distribution": {item["_id"]: item["count"] for item in role_stats},
              "recent_registrations": recent_registrations
          }
  ```

- [ ] **System Configuration Service**
  ```python
  # backend/app/services/config_service.py
  from typing import Any, Dict, Optional
  from ..models.config import SystemConfig, ConfigUpdate
  
  class ConfigService:
      def __init__(self):
          self.db = MongoDB.database
          self.config_collection = "system_config"
      
      async def get_config(self, key: Optional[str] = None) -> Dict[str, Any]:
          """Get system configuration"""
          if key:
              config = await self.db[self.config_collection].find_one({"key": key})
              return config["value"] if config else None
          else:
              cursor = self.db[self.config_collection].find({})
              configs = {}
              async for doc in cursor:
                  configs[doc["key"]] = doc["value"]
              return configs
      
      async def update_config(self, key: str, value: Any) -> bool:
          """Update configuration value"""
          result = await self.db[self.config_collection].update_one(
              {"key": key},
              {
                  "$set": {
                      "value": value,
                      "updated_at": datetime.utcnow(),
                      "updated_by": "admin"  # In real implementation, use current user
                  }
              },
              upsert=True
          )
          return result.acknowledged
      
      async def get_indexing_config(self) -> Dict:
          """Get indexing-specific configuration"""
          indexing_keys = [
              "indexing.enabled_extensions",
              "indexing.chunk_size",
              "indexing.chunk_overlap",
              "indexing.batch_size",
              "indexing.schedule_interval",
              "indexing.max_file_size",
              "indexing.excluded_paths"
          ]
          
          config = {}
          for key in indexing_keys:
              value = await self.get_config(key)
              config[key] = value
          
          return config
      
      async def update_indexing_config(self, config_data: Dict) -> bool:
          """Update indexing configuration"""
          for key, value in config_data.items():
              await self.update_config(key, value)
          return True
      
      async def get_ai_config(self) -> Dict:
          """Get AI-specific configuration"""
          ai_keys = [
              "ai.model_name",
              "ai.temperature",
              "ai.max_tokens",
              "ai.enable_rag",
              "ai.rag_threshold",
              "ai.max_sources"
          ]
          
          config = {}
          for key in ai_keys:
              value = await self.get_config(key)
              config[key] = value
          
          return config
  ```

- [ ] **API Keys Management Service**
  ```python
  # backend/app/services/api_keys_service.py
  from cryptography.fernet import Fernet
  from typing import List, Dict, Optional
  
  class APIKeysService:
      def __init__(self):
          self.db = MongoDB.database
          self.collection = "api_keys"
          self.cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())
      
      async def store_api_key(
          self,
          service_name: str,
          key_name: str,
          api_key: str,
          description: Optional[str] = None
      ) -> bool:
          """Store encrypted API key"""
          encrypted_key = self.cipher_suite.encrypt(api_key.encode()).decode()
          
          key_doc = {
              "service_name": service_name,
              "key_name": key_name,
              "encrypted_key": encrypted_key,
              "description": description,
              "created_at": datetime.utcnow(),
              "updated_at": datetime.utcnow(),
              "is_active": True
          }
          
          result = await self.db[self.collection].update_one(
              {"service_name": service_name, "key_name": key_name},
              {"$set": key_doc},
              upsert=True
          )
          
          return result.acknowledged
      
      async def get_api_key(self, service_name: str, key_name: str) -> Optional[str]:
          """Retrieve and decrypt API key"""
          doc = await self.db[self.collection].find_one({
              "service_name": service_name,
              "key_name": key_name,
              "is_active": True
          })
          
          if doc:
              return self.cipher_suite.decrypt(doc["encrypted_key"].encode()).decode()
          return None
      
      async def list_api_keys(self) -> List[Dict]:
          """List all API keys (without actual key values)"""
          cursor = self.db[self.collection].find(
              {"is_active": True},
              {"encrypted_key": 0}  # Exclude encrypted key from response
          )
          
          keys = []
          async for doc in cursor:
              keys.append({
                  "service_name": doc["service_name"],
                  "key_name": doc["key_name"],
                  "description": doc.get("description", ""),
                  "created_at": doc["created_at"],
                  "updated_at": doc["updated_at"]
              })
          
          return keys
      
      async def delete_api_key(self, service_name: str, key_name: str) -> bool:
          """Soft delete API key"""
          result = await self.db[self.collection].update_one(
              {"service_name": service_name, "key_name": key_name},
              {"$set": {"is_active": False, "deleted_at": datetime.utcnow()}}
          )
          
          return result.modified_count > 0
  ```

### 2. Admin Frontend Components

- [ ] **Admin Layout Component**
  ```typescript
  // src/components/admin/AdminLayout.tsx
  import { useState } from 'react';
  import { Nav, INavLink, Stack, CommandBar, ICommandBarItemProps } from '@fluentui/react';
  import { motion } from 'framer-motion';
  import { useAuth } from '@/hooks/useAuth';
  
  interface AdminLayoutProps {
    children: React.ReactNode;
  }
  
  export const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
    const { user } = useAuth();
    const [selectedKey, setSelectedKey] = useState('dashboard');
    
    const navLinks: INavLink[] = [
      {
        name: 'Dashboard',
        url: '/admin/dashboard',
        key: 'dashboard',
        icon: 'ViewDashboard',
      },
      {
        name: 'Gestione Utenti',
        url: '/admin/users',
        key: 'users',
        icon: 'People',
      },
      {
        name: 'Configurazioni',
        key: 'config',
        icon: 'Settings',
        links: [
          {
            name: 'Impostazioni Generali',
            url: '/admin/config/general',
            key: 'config-general',
          },
          {
            name: 'Configurazione AI',
            url: '/admin/config/ai',
            key: 'config-ai',
          },
          {
            name: 'Indicizzazione',
            url: '/admin/config/indexing',
            key: 'config-indexing',
          },
        ],
      },
      {
        name: 'API Keys',
        url: '/admin/api-keys',
        key: 'api-keys',
        icon: 'SecurityGroup',
      },
      {
        name: 'Monitoraggio',
        key: 'monitoring',
        icon: 'BarChart4',
        links: [
          {
            name: 'Sistema',
            url: '/admin/monitoring/system',
            key: 'monitoring-system',
          },
          {
            name: 'Chat Analytics',
            url: '/admin/monitoring/chat',
            key: 'monitoring-chat',
          },
          {
            name: 'Indicizzazione',
            url: '/admin/monitoring/indexing',
            key: 'monitoring-indexing',
          },
        ],
      },
    ];
    
    const commandBarItems: ICommandBarItemProps[] = [
      {
        key: 'refresh',
        text: 'Aggiorna',
        iconProps: { iconName: 'Refresh' },
        onClick: () => window.location.reload(),
      },
      {
        key: 'export',
        text: 'Esporta Dati',
        iconProps: { iconName: 'Export' },
        onClick: () => console.log('Export data'),
      },
    ];
    
    return (
      <Stack horizontal styles={{ root: { height: '100vh' } }}>
        {/* Sidebar Navigation */}
        <Stack
          styles={{
            root: {
              width: 280,
              backgroundColor: '#f8f9fa',
              borderRight: '1px solid #e1e1e1',
            },
          }}
        >
          <Stack
            styles={{
              root: {
                padding: '20px',
                backgroundColor: '#0078d4',
                color: 'white',
              },
            }}
          >
            <h2>Pannello Admin</h2>
            <p>Benvenuto, {user?.full_name}</p>
          </Stack>
          
          <Nav
            groups={[{ links: navLinks }]}
            selectedKey={selectedKey}
            onLinkClick={(_, item) => setSelectedKey(item?.key || '')}
            styles={{
              root: { padding: '16px' },
            }}
          />
        </Stack>
        
        {/* Main Content */}
        <Stack styles={{ root: { flex: 1, overflow: 'hidden' } }}>
          {/* Command Bar */}
          <CommandBar
            items={commandBarItems}
            styles={{
              root: {
                backgroundColor: 'white',
                borderBottom: '1px solid #e1e1e1',
              },
            }}
          />
          
          {/* Content Area */}
          <Stack
            styles={{
              root: {
                flex: 1,
                padding: '24px',
                overflow: 'auto',
                backgroundColor: '#faf9f8',
              },
            }}
          >
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {children}
            </motion.div>
          </Stack>
        </Stack>
      </Stack>
    );
  };
  ```

- [ ] **Users Management Component**
  ```typescript
  // src/components/admin/UsersManagement.tsx
  import { useState, useEffect } from 'react';
  import {
    DetailsList,
    IColumn,
    CommandBar,
    SearchBox,
    Stack,
    Dialog,
    TextField,
    Dropdown,
    PrimaryButton,
    DefaultButton,
    MessageBar,
    MessageBarType,
  } from '@fluentui/react';
  import { useAdminStore } from '@/store/adminStore';
  import { UserCreateForm } from './UserCreateForm';
  import { UserEditForm } from './UserEditForm';
  
  interface User {
    id: string;
    email: string;
    username: string;
    full_name: string;
    role: 'admin' | 'user' | 'viewer';
    is_active: boolean;
    created_at: string;
    last_login?: string;
  }
  
  export const UsersManagement: React.FC = () => {
    const [searchText, setSearchText] = useState('');
    const [selectedRole, setSelectedRole] = useState<string>('all');
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [selectedUsers, setSelectedUsers] = useState<User[]>([]);
    
    const {
      users,
      isLoading,
      error,
      loadUsers,
      createUser,
      updateUser,
      deleteUser,
      getUserStats,
    } = useAdminStore();
    
    useEffect(() => {
      loadUsers({ search: searchText, role: selectedRole !== 'all' ? selectedRole : undefined });
    }, [searchText, selectedRole, loadUsers]);
    
    const columns: IColumn[] = [
      {
        key: 'email',
        name: 'Email',
        fieldName: 'email',
        minWidth: 200,
        maxWidth: 300,
        isResizable: true,
        onRender: (item: User) => item.email,
      },
      {
        key: 'username',
        name: 'Username',
        fieldName: 'username',
        minWidth: 150,
        maxWidth: 200,
        isResizable: true,
      },
      {
        key: 'full_name',
        name: 'Nome Completo',
        fieldName: 'full_name',
        minWidth: 200,
        maxWidth: 250,
        isResizable: true,
      },
      {
        key: 'role',
        name: 'Ruolo',
        fieldName: 'role',
        minWidth: 100,
        maxWidth: 120,
        onRender: (item: User) => (
          <span style={{
            padding: '4px 8px',
            borderRadius: '4px',
            backgroundColor: 
              item.role === 'admin' ? '#ff4b4b' :
              item.role === 'user' ? '#0078d4' : '#6c757d',
            color: 'white',
            fontSize: '12px',
          }}>
            {item.role.toUpperCase()}
          </span>
        ),
      },
      {
        key: 'is_active',
        name: 'Stato',
        fieldName: 'is_active',
        minWidth: 80,
        maxWidth: 100,
        onRender: (item: User) => (
          <span style={{
            color: item.is_active ? '#107c10' : '#d13438',
            fontWeight: 'bold',
          }}>
            {item.is_active ? 'Attivo' : 'Inattivo'}
          </span>
        ),
      },
      {
        key: 'created_at',
        name: 'Data Creazione',
        fieldName: 'created_at',
        minWidth: 120,
        maxWidth: 150,
        onRender: (item: User) => new Date(item.created_at).toLocaleDateString('it-IT'),
      },
      {
        key: 'last_login',
        name: 'Ultimo Accesso',
        fieldName: 'last_login',
        minWidth: 120,
        maxWidth: 150,
        onRender: (item: User) => 
          item.last_login ? new Date(item.last_login).toLocaleDateString('it-IT') : 'Mai',
      },
    ];
    
    const commandBarItems = [
      {
        key: 'new',
        text: 'Nuovo Utente',
        iconProps: { iconName: 'Add' },
        onClick: () => setShowCreateDialog(true),
      },
      {
        key: 'edit',
        text: 'Modifica',
        iconProps: { iconName: 'Edit' },
        disabled: selectedUsers.length !== 1,
        onClick: () => setEditingUser(selectedUsers[0]),
      },
      {
        key: 'delete',
        text: 'Elimina',
        iconProps: { iconName: 'Delete' },
        disabled: selectedUsers.length === 0,
        onClick: () => handleDeleteUsers(),
      },
      {
        key: 'export',
        text: 'Esporta',
        iconProps: { iconName: 'Export' },
        onClick: () => handleExportUsers(),
      },
    ];
    
    const handleDeleteUsers = async () => {
      if (window.confirm(`Sei sicuro di voler eliminare ${selectedUsers.length} utenti?`)) {
        for (const user of selectedUsers) {
          await deleteUser(user.id);
        }
        setSelectedUsers([]);
        loadUsers();
      }
    };
    
    const handleExportUsers = () => {
      const csv = [
        ['Email', 'Username', 'Nome Completo', 'Ruolo', 'Stato', 'Data Creazione'],
        ...users.map(user => [
          user.email,
          user.username,
          user.full_name,
          user.role,
          user.is_active ? 'Attivo' : 'Inattivo',
          new Date(user.created_at).toLocaleDateString('it-IT'),
        ]),
      ].map(row => row.join(',')).join('\n');
      
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'users.csv';
      a.click();
    };
    
    return (
      <Stack tokens={{ childrenGap: 20 }}>
        <Stack.Item>
          <h1>Gestione Utenti</h1>
        </Stack.Item>
        
        {error && (
          <MessageBar messageBarType={MessageBarType.error}>
            {error}
          </MessageBar>
        )}
        
        {/* Filters */}
        <Stack horizontal tokens={{ childrenGap: 16 }}>
          <SearchBox
            placeholder="Cerca utenti..."
            value={searchText}
            onChange={(_, newValue) => setSearchText(newValue || '')}
            styles={{ root: { width: 300 } }}
          />
          
          <Dropdown
            label="Filtra per ruolo"
            selectedKey={selectedRole}
            onChange={(_, option) => setSelectedRole(option?.key as string)}
            options={[
              { key: 'all', text: 'Tutti i ruoli' },
              { key: 'admin', text: 'Amministratori' },
              { key: 'user', text: 'Utenti' },
              { key: 'viewer', text: 'Visualizzatori' },
            ]}
            styles={{ root: { width: 150 } }}
          />
        </Stack>
        
        {/* Command Bar */}
        <CommandBar items={commandBarItems} />
        
        {/* Users List */}
        <DetailsList
          items={users}
          columns={columns}
          setKey="set"
          layoutMode={0}
          selection={{
            onSelectionChanged: () => {
              const selection = (arguments[0] as any).getSelection() as User[];
              setSelectedUsers(selection);
            },
          }}
          checkboxVisibility={2}
        />
        
        {/* Create User Dialog */}
        <Dialog
          hidden={!showCreateDialog}
          onDismiss={() => setShowCreateDialog(false)}
          dialogContentProps={{
            title: 'Nuovo Utente',
            subText: 'Inserisci i dati del nuovo utente',
          }}
          modalProps={{ isBlocking: true }}
        >
          <UserCreateForm
            onSubmit={async (userData) => {
              await createUser(userData);
              setShowCreateDialog(false);
              loadUsers();
            }}
            onCancel={() => setShowCreateDialog(false)}
          />
        </Dialog>
        
        {/* Edit User Dialog */}
        <Dialog
          hidden={!editingUser}
          onDismiss={() => setEditingUser(null)}
          dialogContentProps={{
            title: 'Modifica Utente',
            subText: `Modifica i dati di ${editingUser?.full_name}`,
          }}
          modalProps={{ isBlocking: true }}
        >
          {editingUser && (
            <UserEditForm
              user={editingUser}
              onSubmit={async (userData) => {
                await updateUser(editingUser.id, userData);
                setEditingUser(null);
                loadUsers();
              }}
              onCancel={() => setEditingUser(null)}
            />
          )}
        </Dialog>
      </Stack>
    );
  };
  ```

### 3. System Configuration Components

- [ ] **General Settings Component**
  ```typescript
  // src/components/admin/GeneralSettings.tsx
  import { useState, useEffect } from 'react';
  import {
    Stack,
    TextField,
    Toggle,
    Dropdown,
    PrimaryButton,
    MessageBar,
    MessageBarType,
    Separator,
  } from '@fluentui/react';
  import { useForm } from 'react-hook-form';
  import { zodResolver } from '@hookform/resolvers/zod';
  import { z } from 'zod';
  import { useConfigStore } from '@/store/configStore';
  
  const settingsSchema = z.object({
    site_name: z.string().min(1, 'Nome sito richiesto'),
    site_description: z.string().optional(),
    max_upload_size: z.number().min(1).max(1000),
    session_timeout: z.number().min(5).max(1440),
    enable_registration: z.boolean(),
    enable_email_verification: z.boolean(),
    default_user_role: z.enum(['user', 'viewer']),
    maintenance_mode: z.boolean(),
  });
  
  type SettingsFormData = z.infer<typeof settingsSchema>;
  
  export const GeneralSettings: React.FC = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    
    const { config, loadConfig, updateConfig } = useConfigStore();
    
    const {
      register,
      handleSubmit,
      reset,
      formState: { errors, isDirty },
    } = useForm<SettingsFormData>({
      resolver: zodResolver(settingsSchema),
    });
    
    useEffect(() => {
      loadConfig();
    }, [loadConfig]);
    
    useEffect(() => {
      if (config) {
        reset({
          site_name: config['site.name'] || '',
          site_description: config['site.description'] || '',
          max_upload_size: config['upload.max_size'] || 10,
          session_timeout: config['auth.session_timeout'] || 60,
          enable_registration: config['auth.enable_registration'] || false,
          enable_email_verification: config['auth.enable_email_verification'] || false,
          default_user_role: config['auth.default_user_role'] || 'user',
          maintenance_mode: config['system.maintenance_mode'] || false,
        });
      }
    }, [config, reset]);
    
    const onSubmit = async (data: SettingsFormData) => {
      setIsLoading(true);
      setMessage(null);
      
      try {
        const configUpdates = {
          'site.name': data.site_name,
          'site.description': data.site_description,
          'upload.max_size': data.max_upload_size,
          'auth.session_timeout': data.session_timeout,
          'auth.enable_registration': data.enable_registration,
          'auth.enable_email_verification': data.enable_email_verification,
          'auth.default_user_role': data.default_user_role,
          'system.maintenance_mode': data.maintenance_mode,
        };
        
        await updateConfig(configUpdates);
        setMessage({ type: 'success', text: 'Configurazioni salvate con successo!' });
      } catch (error) {
        setMessage({ type: 'error', text: 'Errore nel salvare le configurazioni' });
      } finally {
        setIsLoading(false);
      }
    };
    
    return (
      <Stack tokens={{ childrenGap: 20 }}>
        <h1>Impostazioni Generali</h1>
        
        {message && (
          <MessageBar
            messageBarType={message.type === 'success' ? MessageBarType.success : MessageBarType.error}
            onDismiss={() => setMessage(null)}
          >
            {message.text}
          </MessageBar>
        )}
        
        <form onSubmit={handleSubmit(onSubmit)}>
          <Stack tokens={{ childrenGap: 20 }}>
            {/* Site Settings */}
            <Stack tokens={{ childrenGap: 15 }}>
              <h3>Configurazioni Sito</h3>
              
              <TextField
                label="Nome Sito"
                {...register('site_name')}
                errorMessage={errors.site_name?.message}
                required
              />
              
              <TextField
                label="Descrizione Sito"
                multiline
                rows={3}
                {...register('site_description')}
                errorMessage={errors.site_description?.message}
              />
            </Stack>
            
            <Separator />
            
            {/* Upload Settings */}
            <Stack tokens={{ childrenGap: 15 }}>
              <h3>Configurazioni Upload</h3>
              
              <TextField
                label="Dimensione Massima Upload (MB)"
                type="number"
                {...register('max_upload_size', { valueAsNumber: true })}
                errorMessage={errors.max_upload_size?.message}
              />
            </Stack>
            
            <Separator />
            
            {/* Authentication Settings */}
            <Stack tokens={{ childrenGap: 15 }}>
              <h3>Configurazioni Autenticazione</h3>
              
              <TextField
                label="Timeout Sessione (minuti)"
                type="number"
                {...register('session_timeout', { valueAsNumber: true })}
                errorMessage={errors.session_timeout?.message}
              />
              
              <Toggle
                label="Abilita Registrazione Pubblica"
                {...register('enable_registration')}
              />
              
              <Toggle
                label="Abilita Verifica Email"
                {...register('enable_email_verification')}
              />
              
              <Dropdown
                label="Ruolo Utente Predefinito"
                {...register('default_user_role')}
                options={[
                  { key: 'user', text: 'Utente' },
                  { key: 'viewer', text: 'Visualizzatore' },
                ]}
              />
            </Stack>
            
            <Separator />
            
            {/* System Settings */}
            <Stack tokens={{ childrenGap: 15 }}>
              <h3>Configurazioni Sistema</h3>
              
              <Toggle
                label="Modalità Manutenzione"
                {...register('maintenance_mode')}
              />
            </Stack>
            
            <PrimaryButton
              type="submit"
              disabled={!isDirty || isLoading}
              text={isLoading ? 'Salvando...' : 'Salva Configurazioni'}
            />
          </Stack>
        </form>
      </Stack>
    );
  };
  ```

## 📦 Deliverable

### Backend Components
- [ ] Admin APIs per gestione utenti
- [ ] Configuration management system
- [ ] API keys encryption e storage
- [ ] System health monitoring endpoints

### Frontend Components
- [ ] Admin dashboard con analytics
- [ ] Users management interface
- [ ] System settings forms
- [ ] API keys management UI

### Security Features
- [ ] Role-based access control
- [ ] Encrypted storage per API keys
- [ ] Audit logging per admin actions
- [ ] Session management avanzato

### Monitoring & Analytics
- [ ] User activity dashboard
- [ ] System performance metrics
- [ ] Usage analytics
- [ ] Error tracking e reporting

## ✅ Criteri di Completamento

### Funzionali
- ✅ CRUD completo per gestione utenti
- ✅ Configurazioni sistema salvabili via UI
- ✅ API keys gestibili in sicurezza
- ✅ Dashboard analytics funzionante

### Sicurezza
- ✅ Autorizzazione admin-only verificata
- ✅ API keys crittografate correttamente
- ✅ Audit trail per azioni critiche
- ✅ Input validation robusta

### UX/UI
- ✅ Interface intuitiva e responsive
- ✅ Feedback appropriato per azioni
- ✅ Search e filtering funzionanti
- ✅ Export data capabilities

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: Admin Panel Team*