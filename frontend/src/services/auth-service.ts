import { apiClient } from '@/lib/api-client';
import type { LoginRequest, RegisterRequest, LoginResponse, User } from '@/types/auth';

class AuthService {
  /**
   * Effettua il login dell'utente
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
    return response.data;
  }

  /**
   * Registra un nuovo utente
   */
  async register(userData: RegisterRequest): Promise<User> {
    const response = await apiClient.post<User>('/auth/register', userData);
    return response.data;
  }

  /**
   * Ottiene il profilo dell'utente corrente
   */
  async getProfile(): Promise<User> {
    const response = await apiClient.get<User>('/auth/profile');
    return response.data;
  }

  /**
   * Effettua il logout dell'utente
   */
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
  }

  /**
   * Refresh del token di autenticazione
   */
  async refreshToken(refreshToken: string): Promise<string> {
    const response = await apiClient.post<{ token: string }>('/auth/refresh', {
      refreshToken,
    });
    return response.data.token;
  }

  /**
   * Abilita l'autenticazione a due fattori
   */
  async enableMFA(): Promise<{ qrCode: string; secret: string }> {
    const response = await apiClient.post<{ qrCode: string; secret: string }>('/auth/mfa/enable');
    return response.data;
  }

  /**
   * Verifica il codice MFA
   */
  async verifyMFA(token: string): Promise<{ verified: boolean }> {
    const response = await apiClient.post<{ verified: boolean }>('/auth/mfa/verify', {
      token,
    });
    return response.data;
  }

  /**
   * Disabilita l'autenticazione a due fattori
   */
  async disableMFA(password: string): Promise<void> {
    await apiClient.post('/auth/mfa/disable', { password });
  }

  /**
   * Richiede il reset della password
   */
  async requestPasswordReset(email: string): Promise<void> {
    await apiClient.post('/auth/password-reset/request', { email });
  }

  /**
   * Conferma il reset della password
   */
  async confirmPasswordReset(token: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/password-reset/confirm', {
      token,
      newPassword,
    });
  }

  /**
   * Cambia la password dell'utente
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/change-password', {
      currentPassword,
      newPassword,
    });
  }
}

export const authService = new AuthService(); 