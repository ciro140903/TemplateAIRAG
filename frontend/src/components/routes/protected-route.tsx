import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spinner, SpinnerSize, Stack } from '@fluentui/react';
import { useAuthStore } from '@/store/auth-store';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'user' | 'viewer';
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole 
}) => {
  const { isAuthenticated, user, checkAuth, isLoading } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    if (!isAuthenticated && !isLoading) {
      checkAuth();
    }
  }, [isAuthenticated, isLoading, checkAuth]);

  // Mostra loading durante la verifica dell'autenticazione
  if (isLoading) {
    return (
      <Stack
        verticalAlign="center"
        horizontalAlign="center"
        styles={{
          root: {
            height: '100vh',
            backgroundColor: '#faf9f8',
          },
        }}
      >
        <Spinner size={SpinnerSize.large} label="Verifica autenticazione..." />
      </Stack>
    );
  }

  // Se non autenticato, reindirizza al login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Se richiesto un ruolo specifico, verifica i permessi
  if (requiredRole && user?.role !== requiredRole) {
    // Se l'utente non ha i permessi necessari, reindirizza alla dashboard
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}; 