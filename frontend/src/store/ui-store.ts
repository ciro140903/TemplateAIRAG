import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { loadTheme } from '@fluentui/react';
import { lightTheme, darkTheme } from '../lib/fluent-theme';

export type Theme = 'light' | 'dark';

interface UIState {
  theme: Theme;
  sidebarOpen: boolean;
  loading: boolean;
  notifications: Notification[];
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

interface UIStore extends UIState {
  // Theme actions
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
  
  // Sidebar actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  
  // Loading actions
  setLoading: (loading: boolean) => void;
  
  // Notification actions
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  removeNotification: (id: string) => void;
  markNotificationAsRead: (id: string) => void;
  clearNotifications: () => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set, get) => ({
      // Initial state
      theme: 'light',
      sidebarOpen: true,
      loading: false,
      notifications: [],

      // Theme actions
      toggleTheme: () => {
        const currentTheme = get().theme;
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        // Apply Fluent UI theme
        loadTheme(newTheme === 'light' ? lightTheme : darkTheme);
        
        set({ theme: newTheme });
      },

      setTheme: (theme: Theme) => {
        // Apply Fluent UI theme
        loadTheme(theme === 'light' ? lightTheme : darkTheme);
        
        set({ theme });
      },

      // Sidebar actions
      toggleSidebar: () => {
        set((state) => ({ sidebarOpen: !state.sidebarOpen }));
      },

      setSidebarOpen: (open: boolean) => {
        set({ sidebarOpen: open });
      },

      // Loading actions
      setLoading: (loading: boolean) => {
        set({ loading });
      },

      // Notification actions
      addNotification: (notification) => {
        const newNotification: Notification = {
          ...notification,
          id: Date.now().toString(),
          timestamp: new Date(),
          read: false,
        };

        set((state) => ({
          notifications: [newNotification, ...state.notifications].slice(0, 100), // Keep only last 100
        }));
      },

      removeNotification: (id: string) => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }));
      },

      markNotificationAsRead: (id: string) => {
        set((state) => ({
          notifications: state.notifications.map((n) =>
            n.id === id ? { ...n, read: true } : n
          ),
        }));
      },

      clearNotifications: () => {
        set({ notifications: [] });
      },
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          // Apply theme on hydration
          loadTheme(state.theme === 'light' ? lightTheme : darkTheme);
        }
      },
    }
  )
);

// Inizializza il tema Fluent UI al caricamento
if (typeof window !== 'undefined') {
  const store = useUIStore.getState();
  loadTheme(store.theme === 'light' ? lightTheme : darkTheme);
} 