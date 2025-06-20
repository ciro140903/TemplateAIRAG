# Frontend - Portale Aziendale

Frontend moderno costruito con React 18, TypeScript, Tailwind CSS e tecnologie all'avanguardia.

## 🚀 Tecnologie Utilizzate

- **React 18** - Libreria UI moderna con Concurrent Features
- **TypeScript** - Type safety e developer experience superiore
- **Tailwind CSS** - Framework CSS utility-first
- **Framer Motion** - Animazioni fluide e moderne
- **Zustand** - State management leggero e performante
- **React Router** - Routing client-side
- **React Hook Form** - Gestione form performante
- **Zod** - Validazione schema TypeScript-first
- **React Query** - Data fetching e caching intelligente
- **Lucide React** - Icone moderne e consistenti
- **Radix UI** - Componenti UI accessibili
- **Vite** - Build tool veloce e moderno

## 📦 Struttura Progetto

```
src/
├── components/          # Componenti riutilizzabili
│   ├── ui/             # Componenti UI base (Button, Input, etc.)
│   ├── auth/           # Componenti di autenticazione
│   ├── layout/         # Componenti di layout (Header, Sidebar)
│   └── routes/         # Routing e protezione routes
├── pages/              # Pagine dell'applicazione
├── store/              # State management (Zustand stores)
├── services/           # API services e HTTP client
├── types/              # Definizioni TypeScript
├── lib/                # Utilities e configurazioni
└── hooks/              # Custom React hooks
```

## 🛠️ Setup e Installazione

1. **Assicurati di avere Node.js 18+ installato**

2. **Installa le dipendenze:**
   ```bash
   npm install
   ```

3. **Configura le variabili d'ambiente:**
   ```bash
   cp .env.example .env
   ```
   Modifica `.env` con le configurazioni appropriate.

4. **Avvia il server di sviluppo:**
   ```bash
   npm run dev
   ```

5. **Apri il browser su:** http://localhost:3000

## 🔧 Script Disponibili

- `npm run dev` - Avvia il server di sviluppo
- `npm run build` - Build di produzione
- `npm run preview` - Preview del build
- `npm run lint` - Controllo linting

## 🎨 Design System

Il progetto utilizza un design system coerente basato su:

- **Colori:** Palette personalizzata con supporto dark/light mode
- **Typography:** Scale tipografica consistente
- **Spacing:** Sistema di spaziatura modulare
- **Componenti:** Libreria di componenti riutilizzabili

### Componenti UI Principali

- **Button** - Pulsanti con varianti multiple
- **Input** - Campi di input con validazione
- **Card** - Container per contenuti
- **Label** - Etichette per form

## 🔐 Autenticazione

Il sistema di autenticazione include:

- Login/Logout sicuro
- Gestione token JWT
- Protezione routes basata su ruoli
- Persistenza sessione
- Refresh token automatico

### Ruoli Utente

- **Admin** - Accesso completo al sistema
- **User** - Accesso standard alle funzionalità
- **Viewer** - Accesso in sola lettura

## 🎯 Funzionalità Principali

### ✅ Implementate

- [x] Sistema di autenticazione completo
- [x] Dashboard con statistiche
- [x] Layout responsive
- [x] Gestione tema (light/dark)
- [x] Routing protetto
- [x] State management globale
- [x] API client configurato

### 🚧 In Sviluppo

- [ ] Chat AI interface
- [ ] Sistema di upload documenti
- [ ] Pannello amministrativo
- [ ] Analytics dashboard
- [ ] Sistema notifiche

## 🌐 API Integration

Il frontend comunica con il backend tramite:

- **Base URL:** Configurabile via env vars
- **Authentication:** Bearer token
- **Error Handling:** Interceptor automatici
- **Type Safety:** Tipizzazione completa responses

## 📱 Responsive Design

L'applicazione è completamente responsive:

- **Mobile First** - Design ottimizzato per mobile
- **Breakpoints:** Tailwind CSS responsive system
- **Touch Friendly** - Interfaccia ottimizzata touch
- **PWA Ready** - Pronto per Progressive Web App

## 🎨 Theming

Supporto completo per temi:

- **Light Mode** - Tema chiaro default
- **Dark Mode** - Tema scuro
- **System** - Segue le preferenze sistema
- **Personalizzazione** - Variabili CSS custom

## 🧪 Best Practices

Il progetto segue le best practices moderne:

- **TypeScript Strict** - Type safety massima
- **Component Composition** - Architettura modulare
- **Performance** - Lazy loading e code splitting
- **Accessibility** - ARIA labels e keyboard navigation
- **SEO** - Meta tags e structured data

## 📊 Performance

Ottimizzazioni implementate:

- **Bundle Splitting** - Codice diviso per chunk
- **Tree Shaking** - Rimozione codice non utilizzato
- **Image Optimization** - Lazy loading immagini
- **Caching** - React Query per cache intelligente

## 🤝 Contributing

Per contribuire al progetto:

1. Fork del repository
2. Crea un branch feature
3. Implementa le modifiche
4. Testa localmente
5. Submit Pull Request

## 📝 Note di Sviluppo

- Utilizza **ESLint** per il linting
- Segui le convenzioni **TypeScript**
- Testa su multiple viewport
- Verifica accessibilità
- Documenta modifiche significative

---

**Versione:** 1.0.0  
**Ultimo aggiornamento:** Gennaio 2025
