# 🤖 FASE 04: SISTEMA CHAT AI

## 📋 Panoramica Fase

Sviluppo del sistema di chat AI con integrazione Azure OpenAI, cronologia persistente, streaming responses, e interfaccia utente conversazionale avanzata.

## 🎯 Obiettivi

- **Chat Interface Avanzata**: UI conversazionale intuitiva e responsive
- **Streaming Responses**: Risposte AI in tempo reale
- **Cronologia Persistente**: Storage e recupero conversazioni
- **Context Management**: Gestione contesto conversazionale
- **Azure AI Integration**: Integrazione completa GPT-4.1

## ⏱️ Timeline

- **Durata Stimata**: 10-12 giorni
- **Priorità**: ⭐⭐⭐ CRITICA
- **Dipendenze**: Fase 02 (Backend Core), Fase 03 (Frontend Base)
- **Blocca**: Fase 05 (Sistema RAG Avanzato)

## 🛠️ Task Dettagliati

### 1. Backend Chat Services

- [ ] **Enhanced Chat Service**
  ```python
  # backend/app/services/chat_service.py
  class ChatService:
      def __init__(self):
          self.azure_ai = AzureAIService()
          self.db = MongoDB.database
          
      async def create_chat_session(self, user_id: str, title: str = None) -> ChatSession:
          """Crea una nuova sessione di chat"""
          session = ChatSession(
              user_id=ObjectId(user_id),
              title=title or f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}",
          )
          result = await self.db.chat_sessions.insert_one(session.dict(by_alias=True))
          session.id = result.inserted_id
          return session
      
      async def send_message(
          self, 
          session_id: str, 
          user_id: str, 
          message: str,
          stream: bool = True
      ) -> Union[ChatMessage, AsyncGenerator]:
          """Invia messaggio e ottiene risposta AI"""
          
          # Recupera cronologia per contesto
          context = await self.get_conversation_context(session_id, limit=10)
          
          # Prepara messaggi per Azure AI
          messages = self.prepare_messages_for_ai(context, message)
          
          if stream:
              return self.stream_ai_response(session_id, user_id, message, messages)
          else:
              response = await self.azure_ai.generate_response(messages)
              return await self.save_chat_message(session_id, user_id, message, response)
      
      async def stream_ai_response(
          self, 
          session_id: str, 
          user_id: str, 
          user_message: str,
          messages: List[Dict]
      ) -> AsyncGenerator[str, None]:
          """Stream della risposta AI"""
          full_response = ""
          
          async for chunk in self.azure_ai.stream_response(messages):
              if chunk.choices[0].delta.content:
                  content = chunk.choices[0].delta.content
                  full_response += content
                  yield json.dumps({
                      "type": "chunk",
                      "content": content,
                      "session_id": session_id
                  })
          
          # Salva messaggio completo
          await self.save_chat_message(session_id, user_id, user_message, full_response)
          
          yield json.dumps({
              "type": "complete",
              "session_id": session_id,
              "message_id": str(message.id)
          })
      
      async def get_conversation_context(
          self, 
          session_id: str, 
          limit: int = 10
      ) -> List[ChatMessage]:
          """Recupera contesto conversazione"""
          cursor = self.db.chat_messages.find(
              {"session_id": session_id}
          ).sort("timestamp", -1).limit(limit)
          
          messages = []
          async for doc in cursor:
              messages.append(ChatMessage(**doc))
          
          return list(reversed(messages))
  ```

- [ ] **WebSocket Chat Endpoint**
  ```python
  # backend/app/api/v1/chat/websocket.py
  from fastapi import WebSocket, WebSocketDisconnect
  from fastapi.routing import APIRouter
  
  router = APIRouter()
  
  class ConnectionManager:
      def __init__(self):
          self.active_connections: Dict[str, WebSocket] = {}
      
      async def connect(self, websocket: WebSocket, user_id: str):
          await websocket.accept()
          self.active_connections[user_id] = websocket
      
      def disconnect(self, user_id: str):
          if user_id in self.active_connections:
              del self.active_connections[user_id]
      
      async def send_personal_message(self, message: str, user_id: str):
          if user_id in self.active_connections:
              await self.active_connections[user_id].send_text(message)
  
  manager = ConnectionManager()
  
  @router.websocket("/ws/chat/{user_id}")
  async def websocket_chat(websocket: WebSocket, user_id: str):
      await manager.connect(websocket, user_id)
      chat_service = ChatService()
      
      try:
          while True:
              # Ricevi messaggio dal client
              data = await websocket.receive_json()
              
              if data["type"] == "chat_message":
                  session_id = data["session_id"]
                  message = data["message"]
                  
                  # Stream risposta AI
                  async for chunk in chat_service.send_message(
                      session_id, user_id, message, stream=True
                  ):
                      await websocket.send_text(chunk)
              
              elif data["type"] == "ping":
                  await websocket.send_json({"type": "pong"})
                  
      except WebSocketDisconnect:
          manager.disconnect(user_id)
  ```

### 2. Frontend Chat Components

- [ ] **Chat Interface Main Component**
  ```typescript
  // src/components/chat/ChatInterface.tsx
  import { useState, useEffect, useRef } from 'react';
  import { Stack, TextField, IconButton, Spinner } from '@fluentui/react';
  import { motion, AnimatePresence } from 'framer-motion';
  import { useChatStore } from '@/store/chatStore';
  import { ChatMessage } from './ChatMessage';
  import { ChatSidebar } from './ChatSidebar';
  import { useWebSocket } from '@/hooks/useWebSocket';
  
  export const ChatInterface: React.FC = () => {
    const [message, setMessage] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    
    const {
      currentSession,
      messages,
      sessions,
      createSession,
      addMessage,
      updateMessage,
    } = useChatStore();
    
    const { sendMessage, isConnected } = useWebSocket({
      onMessage: handleWebSocketMessage,
      onConnect: () => console.log('Connected to chat'),
      onDisconnect: () => console.log('Disconnected from chat'),
    });
    
    const handleWebSocketMessage = (data: any) => {
      if (data.type === 'chunk') {
        setIsTyping(true);
        updateMessage(data.session_id, data.content, false);
      } else if (data.type === 'complete') {
        setIsTyping(false);
        updateMessage(data.session_id, '', true);
      }
    };
    
    const handleSendMessage = async () => {
      if (!message.trim() || !currentSession) return;
      
      // Aggiungi messaggio utente
      const userMessage = {
        id: Date.now().toString(),
        content: message,
        isUser: true,
        timestamp: new Date(),
      };
      
      addMessage(currentSession.id, userMessage);
      
      // Invia via WebSocket
      sendMessage({
        type: 'chat_message',
        session_id: currentSession.id,
        message: message,
      });
      
      setMessage('');
      
      // Aggiungi placeholder per risposta AI
      const aiMessage = {
        id: (Date.now() + 1).toString(),
        content: '',
        isUser: false,
        timestamp: new Date(),
        isLoading: true,
      };
      
      addMessage(currentSession.id, aiMessage);
    };
    
    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);
    
    return (
      <Stack horizontal styles={{ root: { height: '100vh' } }}>
        <ChatSidebar />
        
        <Stack
          styles={{
            root: {
              flex: 1,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
            },
          }}
        >
          {/* Chat Header */}
          <Stack
            styles={{
              root: {
                padding: '16px 24px',
                borderBottom: '1px solid #e1e1e1',
                backgroundColor: '#faf9f8',
              },
            }}
          >
            <h2>{currentSession?.title || 'Nuova Chat'}</h2>
          </Stack>
          
          {/* Messages Area */}
          <Stack
            styles={{
              root: {
                flex: 1,
                padding: '20px',
                overflowY: 'auto',
                backgroundColor: '#ffffff',
              },
            }}
          >
            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <ChatMessage message={msg} />
                </motion.div>
              ))}
            </AnimatePresence>
            
            {isTyping && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="typing-indicator"
              >
                <Spinner label="L'AI sta scrivendo..." />
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </Stack>
          
          {/* Input Area */}
          <Stack
            horizontal
            styles={{
              root: {
                padding: '16px 24px',
                borderTop: '1px solid #e1e1e1',
                backgroundColor: '#faf9f8',
                alignItems: 'flex-end',
              },
            }}
          >
            <TextField
              multiline
              autoAdjustHeight
              value={message}
              onChange={(_, value) => setMessage(value || '')}
              placeholder="Scrivi il tuo messaggio..."
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              styles={{
                root: { flex: 1, marginRight: '12px' },
                field: { maxHeight: '120px' },
              }}
            />
            
            <IconButton
              iconProps={{ iconName: 'Send' }}
              title="Invia messaggio"
              disabled={!message.trim() || !isConnected}
              onClick={handleSendMessage}
              styles={{
                root: {
                  backgroundColor: '#0078d4',
                  color: 'white',
                  width: '44px',
                  height: '44px',
                },
              }}
            />
          </Stack>
        </Stack>
      </Stack>
    );
  };
  ```

- [ ] **Chat Message Component**
  ```typescript
  // src/components/chat/ChatMessage.tsx
  import { useState } from 'react';
  import { Stack, IconButton, Text, Callout } from '@fluentui/react';
  import { motion } from 'framer-motion';
  import ReactMarkdown from 'react-markdown';
  import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
  import { vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
  
  interface ChatMessageProps {
    message: {
      id: string;
      content: string;
      isUser: boolean;
      timestamp: Date;
      isLoading?: boolean;
      sources?: Array<{ title: string; url: string }>;
    };
  }
  
  export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
    const [showSources, setShowSources] = useState(false);
    const [copied, setCopied] = useState(false);
    
    const handleCopy = async () => {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Stack
          styles={{
            root: {
              marginBottom: '16px',
              alignItems: message.isUser ? 'flex-end' : 'flex-start',
            },
          }}
        >
          <Stack
            styles={{
              root: {
                maxWidth: '80%',
                padding: '12px 16px',
                borderRadius: '8px',
                backgroundColor: message.isUser ? '#0078d4' : '#f3f2f1',
                color: message.isUser ? 'white' : '#323130',
                position: 'relative',
              },
            }}
          >
            {message.isLoading ? (
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <Text>●●●</Text>
              </motion.div>
            ) : (
              <>
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <SyntaxHighlighter
                          style={vs}
                          language={match[1]}
                          PreTag="div"
                          {...props}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
                
                {!message.isUser && (
                  <Stack horizontal tokens={{ childrenGap: 8 }} styles={{ root: { marginTop: '8px' } }}>
                    <IconButton
                      iconProps={{ iconName: 'Copy' }}
                      title={copied ? 'Copiato!' : 'Copia messaggio'}
                      onClick={handleCopy}
                      styles={{ root: { color: '#605e5c' } }}
                    />
                    
                    {message.sources && message.sources.length > 0 && (
                      <IconButton
                        iconProps={{ iconName: 'Source' }}
                        title="Mostra fonti"
                        onClick={() => setShowSources(!showSources)}
                        styles={{ root: { color: '#605e5c' } }}
                      />
                    )}
                  </Stack>
                )}
                
                {showSources && message.sources && (
                  <Callout
                    target={`.message-${message.id}`}
                    onDismiss={() => setShowSources(false)}
                    directionalHint={6}
                  >
                    <Stack tokens={{ childrenGap: 8 }} styles={{ root: { padding: '16px' } }}>
                      <Text variant="mediumPlus">Fonti:</Text>
                      {message.sources.map((source, index) => (
                        <Stack key={index} horizontal tokens={{ childrenGap: 8 }}>
                          <IconButton iconProps={{ iconName: 'Link' }} />
                          <Text styles={{ root: { textDecoration: 'underline', cursor: 'pointer' } }}>
                            {source.title}
                          </Text>
                        </Stack>
                      ))}
                    </Stack>
                  </Callout>
                )}
              </>
            )}
            
            <Text
              variant="tiny"
              styles={{
                root: {
                  marginTop: '4px',
                  opacity: 0.7,
                  fontSize: '11px',
                },
              }}
            >
              {message.timestamp.toLocaleTimeString()}
            </Text>
          </Stack>
        </Stack>
      </motion.div>
    );
  };
  ```

### 3. State Management per Chat

- [ ] **Chat Store (Zustand)**
  ```typescript
  // src/store/chatStore.ts
  import { create } from 'zustand';
  import { persist } from 'zustand/middleware';
  import { chatService } from '@/services/chatService';
  
  interface ChatMessage {
    id: string;
    content: string;
    isUser: boolean;
    timestamp: Date;
    isLoading?: boolean;
    sources?: Array<{ title: string; url: string }>;
  }
  
  interface ChatSession {
    id: string;
    title: string;
    createdAt: Date;
    updatedAt: Date;
    messageCount: number;
  }
  
  interface ChatState {
    sessions: ChatSession[];
    currentSession: ChatSession | null;
    messages: { [sessionId: string]: ChatMessage[] };
    isLoading: boolean;
    
    // Actions
    loadSessions: () => Promise<void>;
    createSession: (title?: string) => Promise<ChatSession>;
    selectSession: (sessionId: string) => Promise<void>;
    deleteSession: (sessionId: string) => Promise<void>;
    addMessage: (sessionId: string, message: ChatMessage) => void;
    updateMessage: (sessionId: string, content: string, isComplete: boolean) => void;
    clearMessages: (sessionId: string) => void;
  }
  
  export const useChatStore = create<ChatState>()(
    persist(
      (set, get) => ({
        sessions: [],
        currentSession: null,
        messages: {},
        isLoading: false,
        
        loadSessions: async () => {
          set({ isLoading: true });
          try {
            const sessions = await chatService.getSessions();
            set({ sessions, isLoading: false });
          } catch (error) {
            console.error('Error loading sessions:', error);
            set({ isLoading: false });
          }
        },
        
        createSession: async (title) => {
          try {
            const session = await chatService.createSession(title);
            set((state) => ({
              sessions: [session, ...state.sessions],
              currentSession: session,
              messages: { ...state.messages, [session.id]: [] },
            }));
            return session;
          } catch (error) {
            console.error('Error creating session:', error);
            throw error;
          }
        },
        
        selectSession: async (sessionId) => {
          const { sessions, messages } = get();
          const session = sessions.find(s => s.id === sessionId);
          
          if (session) {
            set({ currentSession: session });
            
            // Carica messaggi se non già in cache
            if (!messages[sessionId]) {
              try {
                const sessionMessages = await chatService.getMessages(sessionId);
                set((state) => ({
                  messages: { ...state.messages, [sessionId]: sessionMessages },
                }));
              } catch (error) {
                console.error('Error loading messages:', error);
              }
            }
          }
        },
        
        deleteSession: async (sessionId) => {
          try {
            await chatService.deleteSession(sessionId);
            set((state) => {
              const newSessions = state.sessions.filter(s => s.id !== sessionId);
              const newMessages = { ...state.messages };
              delete newMessages[sessionId];
              
              return {
                sessions: newSessions,
                messages: newMessages,
                currentSession: state.currentSession?.id === sessionId ? null : state.currentSession,
              };
            });
          } catch (error) {
            console.error('Error deleting session:', error);
            throw error;
          }
        },
        
        addMessage: (sessionId, message) => {
          set((state) => ({
            messages: {
              ...state.messages,
              [sessionId]: [...(state.messages[sessionId] || []), message],
            },
          }));
        },
        
        updateMessage: (sessionId, content, isComplete) => {
          set((state) => {
            const sessionMessages = state.messages[sessionId] || [];
            const lastMessage = sessionMessages[sessionMessages.length - 1];
            
            if (lastMessage && !lastMessage.isUser) {
              const updatedMessage = {
                ...lastMessage,
                content: isComplete ? content : lastMessage.content + content,
                isLoading: !isComplete,
              };
              
              return {
                messages: {
                  ...state.messages,
                  [sessionId]: [
                    ...sessionMessages.slice(0, -1),
                    updatedMessage,
                  ],
                },
              };
            }
            
            return state;
          });
        },
        
        clearMessages: (sessionId) => {
          set((state) => ({
            messages: { ...state.messages, [sessionId]: [] },
          }));
        },
      }),
      {
        name: 'chat-storage',
        partialize: (state) => ({
          sessions: state.sessions,
          currentSession: state.currentSession,
        }),
      }
    )
  );
  ```

### 4. WebSocket Hook

- [ ] **useWebSocket Hook**
  ```typescript
  // src/hooks/useWebSocket.ts
  import { useEffect, useRef, useState } from 'react';
  import { useAuthStore } from '@/store/authStore';
  
  interface UseWebSocketOptions {
    onMessage: (data: any) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    onError?: (error: Event) => void;
  }
  
  export const useWebSocket = (options: UseWebSocketOptions) => {
    const [isConnected, setIsConnected] = useState(false);
    const [reconnectAttempts, setReconnectAttempts] = useState(0);
    const ws = useRef<WebSocket | null>(null);
    const reconnectTimeout = useRef<NodeJS.Timeout>();
    const { user, token } = useAuthStore();
    
    const connect = () => {
      if (!user || !token) return;
      
      const wsUrl = `${process.env.REACT_APP_WS_URL}/ws/chat/${user.id}?token=${token}`;
      ws.current = new WebSocket(wsUrl);
      
      ws.current.onopen = () => {
        setIsConnected(true);
        setReconnectAttempts(0);
        options.onConnect?.();
      };
      
      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          options.onMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.current.onclose = () => {
        setIsConnected(false);
        options.onDisconnect?.();
        
        // Reconnect logic
        if (reconnectAttempts < 5) {
          reconnectTimeout.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connect();
          }, Math.pow(2, reconnectAttempts) * 1000); // Exponential backoff
        }
      };
      
      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        options.onError?.(error);
      };
    };
    
    const disconnect = () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      ws.current?.close();
    };
    
    const sendMessage = (data: any) => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify(data));
      } else {
        console.warn('WebSocket is not connected');
      }
    };
    
    useEffect(() => {
      if (user && token) {
        connect();
      }
      
      return () => {
        disconnect();
      };
    }, [user, token]);
    
    return { sendMessage, isConnected, disconnect };
  };
  ```

## 📦 Deliverable

### Backend Components
- [ ] Chat service con streaming support
- [ ] WebSocket endpoints per real-time chat
- [ ] Cronologia chat persistente
- [ ] Context management per conversazioni

### Frontend Components
- [ ] Chat interface responsive
- [ ] Message streaming con typing indicators
- [ ] Sidebar con sessioni chat
- [ ] Markdown rendering per risposte AI

### Features Avanzate
- [ ] Copy/paste messaggi
- [ ] Search nella cronologia
- [ ] Export conversazioni
- [ ] Feedback system per risposte

## ✅ Criteri di Completamento

### Funzionali
- ✅ Chat streaming funzionante
- ✅ Cronologia persistente
- ✅ WebSocket connection stabile
- ✅ Context management operativo

### Performance
- ✅ Latenza streaming < 100ms
- ✅ Memory usage ottimizzato
- ✅ Reconnection automatica
- ✅ Messaggi non persi durante reconnect

### UX
- ✅ Typing indicators fluidi
- ✅ Scroll automatico
- ✅ Responsive su mobile
- ✅ Keyboard shortcuts

---

*📅 Ultimo aggiornamento: [Data]*  
*👤 Responsabile: AI Development Team* 