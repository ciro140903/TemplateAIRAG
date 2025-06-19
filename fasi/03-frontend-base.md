# 🎨 FASE 03: FRONTEND BASE

## 📋 Panoramica Fase

Sviluppo del frontend React con TypeScript, Microsoft Fluent UI, setup dell'architettura components, routing, state management e integrazione con le API backend.

## 🎯 Obiettivi

- **React App Moderna**: Setup con TypeScript e best practices
- **Design System**: Implementazione Microsoft Fluent UI
- **Architecture Scalabile**: Struttura componenti e state management
- **Authentication UI**: Interfacce login, registrazione, MFA
- **Responsive Design**: Mobile-first con animazioni fluide

## ⏱️ Timeline

- **Durata Stimata**: 6-8 giorni
- **Priorità**: ⭐⭐⭐ CRITICA
- **Dipendenze**: Fase 01 (Setup Infrastrutturale)
- **Parallelo con**: Fase 02 (Backend Core)

## 🛠️ Task Dettagliati

### 1. Setup Progetto React

- [ ] **Create React App con TypeScript**
  ```bash
  npx create-react-app frontend --template typescript
  cd frontend
  ```

- [ ] **Struttura Progetto**
  ```
  frontend/
  ├── src/
  │   ├── components/
  │   │   ├── ui/           # Fluent UI customized components
  │   │   ├── layout/       # Layout components
  │   │   ├── forms/        # Form components
  │   │   └── features/     # Feature-specific components
  │   ├── pages/
  │   │   ├── auth/
  │   │   ├── chat/
  │   │   ├── admin/
  │   │   └── dashboard/
  │   ├── hooks/            # Custom React hooks
  │   ├── services/         # API services
  │   ├── store/            # State management
  │   ├── types/            # TypeScript definitions
  │   ├── utils/            # Helper functions
  │   └── assets/
  ├── public/
  └── package.json
  ```

### 2. Dipendenze e Setup

- [ ] **Core Dependencies**
  ```json
  {
    "dependencies": {
      "@fluentui/react": "^8.110.0",
      "@fluentui/react-icons": "^2.0.220",
      "@fluentui/react-components": "^9.46.0",
      "react": "^18.2.0",
      "react-router-dom": "^6.20.0",
      "react-query": "^3.39.0",
      "framer-motion": "^10.16.0",
      "axios": "^1.6.0",
      "zustand": "^4.4.0",
      "react-hook-form": "^7.48.0",
      "@hookform/resolvers": "^3.3.0",
      "zod": "^3.22.0"
    },
    "devDependencies": {
      "@types/react": "^18.2.0",
      "@types/react-dom": "^18.2.0",
      "tailwindcss": "^3.3.0",
      "autoprefixer": "^10.4.0",
      "postcss": "^8.4.0"
    }
  }
  ```

- [ ] **Configurazione TypeScript**
  ```json
  // tsconfig.json
  {
    "compilerOptions": {
      "target": "ES2020",
      "lib": ["DOM", "DOM.Iterable", "ES6"],
      "allowJs": true,
      "skipLibCheck": true,
      "esModuleInterop": true,
      "allowSyntheticDefaultImports": true,
      "strict": true,
      "forceConsistentCasingInFileNames": true,
      "moduleResolution": "node",
      "resolveJsonModule": true,
      "isolatedModules": true,
      "noEmit": true,
      "jsx": "react-jsx",
      "baseUrl": "src",
      "paths": {
        "@/*": ["*"],
        "@/components/*": ["components/*"],
        "@/pages/*": ["pages/*"],
        "@/services/*": ["services/*"],
        "@/types/*": ["types/*"]
      }
    }
  }
  ```

### 3. Microsoft Fluent UI Setup

- [ ] **Theme Configuration**
  ```typescript
  // src/theme/fluentTheme.ts
  import { createTheme, Theme } from '@fluentui/react';
  
  export const lightTheme: Theme = createTheme({
    palette: {
      themePrimary: '#0078d4',
      themeLighterAlt: '#eff6fc',
      themeLighter: '#deecf9',
      themeLight: '#c7e0f4',
      themeTertiary: '#71afe5',
      themeSecondary: '#2b88d8',
      themeDarkAlt: '#106ebe',
      themeDark: '#005a9e',
      themeDarker: '#004578',
    },
    fonts: {
      small: { fontSize: '12px' },
      medium: { fontSize: '14px' },
      large: { fontSize: '16px' },
      xLarge: { fontSize: '20px' },
    },
  });
  
  export const darkTheme: Theme = createTheme({
    // Dark theme configuration
  });
  ```

- [ ] **Theme Provider Setup**
  ```typescript
  // src/App.tsx
  import { ThemeProvider } from '@fluentui/react';
  import { useTheme } from './hooks/useTheme';
  
  export const App: React.FC = () => {
    const { theme, toggleTheme } = useTheme();
    
    return (
      <ThemeProvider theme={theme}>
        <Router>
          <Layout>
            <AppRoutes />
          </Layout>
        </Router>
      </ThemeProvider>
    );
  };
  ```

### 4. Routing e Navigation

- [ ] **Router Configuration**
  ```typescript
  // src/routes/AppRoutes.tsx
  import { Routes, Route, Navigate } from 'react-router-dom';
  import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
  
  export const AppRoutes: React.FC = () => {
    return (
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Protected Routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        } />
        
        <Route path="/chat" element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        } />
        
        <Route path="/admin/*" element={
          <ProtectedRoute requiredRole="admin">
            <AdminRoutes />
          </ProtectedRoute>
        } />
        
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    );
  };
  ```

- [ ] **Navigation Component**
  ```typescript
  // src/components/layout/Navigation.tsx
  import { Nav, INavLink } from '@fluentui/react';
  import { useAuth } from '@/hooks/useAuth';
  
  export const Navigation: React.FC = () => {
    const { user } = useAuth();
    
    const navLinks: INavLink[] = [
      {
        name: 'Dashboard',
        url: '/dashboard',
        icon: 'Home',
      },
      {
        name: 'Chat AI',
        url: '/chat',
        icon: 'Chat',
      },
      ...(user?.role === 'admin' ? [{
        name: 'Amministrazione',
        url: '/admin',
        icon: 'Settings',
      }] : []),
    ];
    
    return (
      <Nav
        groups={[{ links: navLinks }]}
        styles={{
          root: { width: 250 },
        }}
      />
    );
  };
  ```

### 5. State Management (Zustand)

- [ ] **Auth Store**
  ```typescript
  // src/store/authStore.ts
  import { create } from 'zustand';
  import { persist } from 'zustand/middleware';
  
  interface User {
    id: string;
    email: string;
    username: string;
    role: 'admin' | 'user' | 'viewer';
    mfaEnabled: boolean;
  }
  
  interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    updateUser: (user: User) => void;
  }
  
  export const useAuthStore = create<AuthState>()(
    persist(
      (set, get) => ({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        
        login: async (email: string, password: string) => {
          set({ isLoading: true });
          try {
            const response = await authService.login(email, password);
            set({
              user: response.user,
              token: response.token,
              isAuthenticated: true,
              isLoading: false,
            });
          } catch (error) {
            set({ isLoading: false });
            throw error;
          }
        },
        
        logout: () => {
          set({ user: null, token: null, isAuthenticated: false });
          authService.logout();
        },
        
        updateUser: (user: User) => {
          set({ user });
        },
      }),
      {
        name: 'auth-storage',
      }
    )
  );
  ```

- [ ] **UI State Store**
  ```typescript
  // src/store/uiStore.ts
  import { create } from 'zustand';
  
  interface UIState {
    theme: 'light' | 'dark';
    sidebarCollapsed: boolean;
    notifications: Notification[];
    toggleTheme: () => void;
    toggleSidebar: () => void;
    addNotification: (notification: Notification) => void;
    removeNotification: (id: string) => void;
  }
  
  export const useUIStore = create<UIState>((set) => ({
    theme: 'light',
    sidebarCollapsed: false,
    notifications: [],
    
    toggleTheme: () => set((state) => ({ 
      theme: state.theme === 'light' ? 'dark' : 'light' 
    })),
    
    toggleSidebar: () => set((state) => ({ 
      sidebarCollapsed: !state.sidebarCollapsed 
    })),
    
    addNotification: (notification) => set((state) => ({
      notifications: [...state.notifications, notification]
    })),
    
    removeNotification: (id) => set((state) => ({
      notifications: state.notifications.filter(n => n.id !== id)
    })),
  }));
  ```

### 6. API Services Layer

- [ ] **HTTP Client Setup**
  ```typescript
  // src/services/apiClient.ts
  import axios, { AxiosResponse } from 'axios';
  import { useAuthStore } from '@/store/authStore';
  
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
  
  export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  // Request interceptor per aggiungere token
  apiClient.interceptors.request.use((config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  
  // Response interceptor per gestire errori
  apiClient.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
      if (error.response?.status === 401) {
        useAuthStore.getState().logout();
      }
      return Promise.reject(error);
    }
  );
  ```

- [ ] **Auth Service**
  ```typescript
  // src/services/authService.ts
  import { apiClient } from './apiClient';
  
  interface LoginRequest {
    email: string;
    password: string;
  }
  
  interface LoginResponse {
    user: User;
    token: string;
    refreshToken: string;
  }
  
  class AuthService {
    async login(email: string, password: string): Promise<LoginResponse> {
      const response = await apiClient.post('/auth/login', { email, password });
      return response.data;
    }
    
    async register(userData: RegisterRequest): Promise<User> {
      const response = await apiClient.post('/auth/register', userData);
      return response.data;
    }
    
    async refreshToken(refreshToken: string): Promise<string> {
      const response = await apiClient.post('/auth/refresh', { refreshToken });
      return response.data.token;
    }
    
    async logout(): Promise<void> {
      await apiClient.post('/auth/logout');
    }
    
    async enableMFA(): Promise<{ qrCode: string; secret: string }> {
      const response = await apiClient.post('/auth/mfa/enable');
      return response.data;
    }
    
    async verifyMFA(token: string): Promise<boolean> {
      const response = await apiClient.post('/auth/mfa/verify', { token });
      return response.data.verified;
    }
  }
  
  export const authService = new AuthService();
  ```

### 7. Authentication Components

- [ ] **Login Component**
  ```typescript
  // src/components/auth/LoginForm.tsx
  import { useState } from 'react';
  import { useForm } from 'react-hook-form';
  import { zodResolver } from '@hookform/resolvers/zod';
  import { z } from 'zod';
  import {
    Stack,
    TextField,
    PrimaryButton,
    DefaultButton,
    MessageBar,
    MessageBarType,
  } from '@fluentui/react';
  import { motion } from 'framer-motion';
  
  const loginSchema = z.object({
    email: z.string().email('Email non valida'),
    password: z.string().min(8, 'Password deve essere di almeno 8 caratteri'),
  });
  
  type LoginFormData = z.infer<typeof loginSchema>;
  
  export const LoginForm: React.FC = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { login } = useAuthStore();
    
    const {
      register,
      handleSubmit,
      formState: { errors, isValid },
    } = useForm<LoginFormData>({
      resolver: zodResolver(loginSchema),
      mode: 'onChange',
    });
    
    const onSubmit = async (data: LoginFormData) => {
      setIsLoading(true);
      setError(null);
      
      try {
        await login(data.email, data.password);
      } catch (err) {
        setError('Credenziali non valide');
      } finally {
        setIsLoading(false);
      }
    };
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Stack tokens={{ childrenGap: 20 }}>
          {error && (
            <MessageBar messageBarType={MessageBarType.error}>
              {error}
            </MessageBar>
          )}
          
          <form onSubmit={handleSubmit(onSubmit)}>
            <Stack tokens={{ childrenGap: 15 }}>
              <TextField
                label="Email"
                type="email"
                {...register('email')}
                errorMessage={errors.email?.message}
                required
              />
              
              <TextField
                label="Password"
                type="password"
                {...register('password')}
                errorMessage={errors.password?.message}
                required
              />
              
              <Stack horizontal tokens={{ childrenGap: 10 }}>
                <PrimaryButton
                  type="submit"
                  disabled={!isValid || isLoading}
                  text={isLoading ? 'Accesso in corso...' : 'Accedi'}
                />
                <DefaultButton
                  text="Registrati"
                  onClick={() => navigate('/register')}
                />
              </Stack>
            </Stack>
          </form>
        </Stack>
      </motion.div>
    );
  };
  ```

### 8. Layout Components

- [ ] **Main Layout**
  ```typescript
  // src/components/layout/MainLayout.tsx
  import { Stack, Panel, IconButton } from '@fluentui/react';
  import { Navigation } from './Navigation';
  import { Header } from './Header';
  import { useUIStore } from '@/store/uiStore';
  import { motion, AnimatePresence } from 'framer-motion';
  
  interface MainLayoutProps {
    children: React.ReactNode;
  }
  
  export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
    const { sidebarCollapsed, toggleSidebar } = useUIStore();
    
    return (
      <Stack
        styles={{
          root: {
            height: '100vh',
            overflow: 'hidden',
          },
        }}
      >
        <Header />
        
        <Stack horizontal styles={{ root: { flex: 1 } }}>
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 250, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                style={{ overflow: 'hidden' }}
              >
                <Navigation />
              </motion.div>
            )}
          </AnimatePresence>
          
          <Stack
            styles={{
              root: {
                flex: 1,
                padding: '20px',
                overflow: 'auto',
              },
            }}
          >
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.2 }}
            >
              {children}
            </motion.div>
          </Stack>
        </Stack>
      </Stack>
    );
  };
  ```

## 📦 Deliverable

### Core Application
- [ ] React app con TypeScript configurato
- [ ] Microsoft Fluent UI theme e componenti
- [ ] Router con protezione routes
- [ ] State management con Zustand

### Authentication System
- [ ] Login/Register forms con validazione
- [ ] Protected routes component
- [ ] Token management automatico
- [ ] MFA interface base

### UI/UX Components
- [ ] Layout responsive
- [ ] Navigation component
- [ ] Theme switching (light/dark)
- [ ] Loading states e error handling

### Development Tools
- [ ] TypeScript configurazione strict
- [ ] ESLint e Prettier setup
- [ ] API client con interceptors
- [ ] Custom hooks per features comuni

## ✅ Criteri di Completamento

### Funzionali
- ✅ Login/logout funzionante
- ✅ Navigation tra pages protected
- ✅ Theme switching operativo
- ✅ Responsive design verificato

### Tecnici
- ✅ TypeScript senza errori
- ✅ Bundle size < 2MB (gzipped)
- ✅ Performance Lighthouse > 90
- ✅ Accessibility score > 90

### UX/UI
- ✅ Design coerente con Fluent UI
- ✅ Animazioni fluide
- ✅ Loading states appropriati
- ✅ Error handling user-friendly

## 🚨 Rischi e Mitigazioni

### Rischi Tecnici
- **Bundle Size**: Code splitting e lazy loading
- **Performance**: React.memo e optimization
- **Compatibility**: Testing su browser multipli

### Rischi UX
- **Learning Curve Fluent UI**: Documentazione e examples
- **Responsive Issues**: Mobile-first testing
- **Accessibility**: Screen reader testing

## 🔗 Dipendenze

### Esterne
- **Node.js 18+**: Runtime environment
- **Backend APIs**: Fase 02 completata
- **Design Assets**: Logo e branding assets

### Interne
- **Fase 01**: Infrastruttura per hosting
- **Environment Variables**: API endpoints configurati

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: Frontend Development Team* 