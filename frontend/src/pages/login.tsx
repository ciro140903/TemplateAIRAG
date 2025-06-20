import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Stack, Text, FontWeights } from '@fluentui/react';
import { LoginForm } from '@/components/auth/login-form';
import { useAuthStore } from '@/store/auth-store';

export const LoginPage: React.FC = () => {
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Se l'utente è già autenticato, reindirizza alla dashboard
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px'
    }}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        style={{
          width: '100%',
          maxWidth: '480px'
        }}
      >
        <Stack tokens={{ childrenGap: 32 }}>
          {/* Logo/Brand Section */}
          <Stack horizontalAlign="center" tokens={{ childrenGap: 16 }}>
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              style={{
                width: '72px',
                height: '72px',
                backgroundColor: '#0078d4',
                borderRadius: '20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 8px 32px rgba(0, 120, 212, 0.3)',
                marginBottom: '8px'
              }}
            >
              <Text 
                styles={{ 
                  root: { 
                    color: '#ffffff',
                    fontWeight: FontWeights.bold,
                    fontSize: '28px'
                  } 
                }}
              >
                P
              </Text>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              style={{ textAlign: 'center' }}
            >
              <Text 
                variant="xxLarge" 
                styles={{ 
                  root: { 
                    fontWeight: FontWeights.semibold,
                    color: '#323130',
                    marginBottom: '8px'
                  } 
                }}
              >
                Portale Aziendale
              </Text>
              <Text 
                variant="large" 
                styles={{ 
                  root: { 
                    color: '#605e5c'
                  } 
                }}
              >
                Sistema di gestione documentale e AI
              </Text>
            </motion.div>
          </Stack>

          {/* Login Form */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <LoginForm />
          </motion.div>
        </Stack>
      </motion.div>
    </div>
  );
}; 