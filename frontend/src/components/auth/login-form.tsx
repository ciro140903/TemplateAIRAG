import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import {
  Stack,
  TextField,
  PrimaryButton,
  DefaultButton,
  MessageBar,
  MessageBarType,
  Text,
  FontWeights,
  IStackTokens,
  IconButton,
} from '@fluentui/react';
import { useAuthStore } from '@/store/auth-store';
import { useUIStore } from '@/store/ui-store';

const loginSchema = z.object({
  email: z.string().email('Inserisci un email valida'),
  password: z.string().min(8, 'La password deve essere di almeno 8 caratteri'),
});

type LoginFormData = z.infer<typeof loginSchema>;

const stackTokens: IStackTokens = { childrenGap: 20 };
const formStackTokens: IStackTokens = { childrenGap: 15 };

export const LoginForm: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const { login, isLoading } = useAuthStore();
  const { addNotification } = useUIStore();

  const {
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onChange',
  });

  const watchedEmail = watch('email');
  const watchedPassword = watch('password');

  const onSubmit = async (data: LoginFormData) => {
    setError(null);
    
    try {
      await login(data);
      addNotification({
        type: 'success',
        title: 'Login effettuato',
        message: 'Benvenuto nel portale!',
      });
      navigate('/dashboard');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Credenziali non valide';
      setError(errorMessage);
      addNotification({
        type: 'error',
        title: 'Errore di login',
        message: errorMessage,
      });
    }
  };

  return (
    <div style={{ 
      backgroundColor: 'white',
      padding: '40px',
      borderRadius: '12px',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
      border: '1px solid #e1dfdd'
    }}>
        <Stack tokens={stackTokens}>
          <Stack horizontalAlign="center" tokens={{ childrenGap: 10 }}>
            <Text variant="xxLarge" styles={{ root: { fontWeight: FontWeights.semibold } }}>
              Accedi al Portale
            </Text>
            <Text variant="medium" styles={{ root: { color: '#605e5c' } }}>
              Inserisci le tue credenziali per accedere
            </Text>
          </Stack>
          
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
            >
              <MessageBar messageBarType={MessageBarType.error}>
                {error}
              </MessageBar>
            </motion.div>
          )}

          <form onSubmit={handleSubmit(onSubmit)}>
            <Stack tokens={formStackTokens}>
              <TextField
                label="Email"
                type="email"
                placeholder="nome@esempio.com"
                value={watchedEmail || ''}
                onChange={(_, newValue) => setValue('email', newValue || '')}
                errorMessage={errors.email?.message}
                required
              />
              
              <TextField
                label="Password"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={watchedPassword || ''}
                onChange={(_, newValue) => setValue('password', newValue || '')}
                errorMessage={errors.password?.message}
                onRenderSuffix={() => (
                  <IconButton
                    iconProps={{ iconName: showPassword ? 'Hide' : 'RedEye' }}
                    onClick={() => setShowPassword(!showPassword)}
                    ariaLabel={showPassword ? 'Nascondi password' : 'Mostra password'}
                  />
                )}
                required
              />

              <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
                <Link
                  to="/forgot-password"
                  style={{ 
                    textDecoration: 'none', 
                    color: '#0078d4',
                    fontSize: '14px'
                  }}
                >
                  Password dimenticata?
                </Link>
              </Stack>

              <Stack horizontal tokens={{ childrenGap: 10 }}>
                <PrimaryButton
                  type="submit"
                  disabled={!isValid || isLoading}
                  text={isLoading ? 'Accesso in corso...' : 'Accedi'}
                  iconProps={!isLoading ? { iconName: 'SignIn' } : undefined}
                  styles={{ root: { flex: 1 } }}
                />
                <DefaultButton
                  text="Registrati"
                  onClick={() => navigate('/register')}
                  iconProps={{ iconName: 'AddFriend' }}
                  styles={{ root: { flex: 1 } }}
                />
              </Stack>

              <Stack horizontalAlign="center">
                <Text variant="small" styles={{ root: { color: '#605e5c' } }}>
                  Non hai un account?{' '}
                  <Link 
                    to="/register" 
                    style={{ 
                      color: '#0078d4', 
                      textDecoration: 'none',
                      fontWeight: FontWeights.semibold
                    }}
                  >
                    Registrati
                  </Link>
                </Text>
              </Stack>
            </Stack>
          </form>
        </Stack>
    </div>
  );
}; 