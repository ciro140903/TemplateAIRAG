
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, initializeIcons } from '@fluentui/react';
import { AppRoutes } from '@/components/routes/app-routes';
import { useUIStore } from '@/store/ui-store';
import { lightTheme, darkTheme } from '@/lib/fluent-theme';

// Inizializza le icone Fluent UI
initializeIcons();

// Crea l'istanza del QueryClient per React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const { theme } = useUIStore();
  const currentTheme = theme === 'dark' ? darkTheme : lightTheme;

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider theme={currentTheme}>
          <div style={{ height: '100vh' }}>
            <AppRoutes />
          </div>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
