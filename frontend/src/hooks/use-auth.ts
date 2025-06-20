import { useAuthStore } from '@/store/auth-store';

/**
 * Custom hook per gestire l'autenticazione
 * Fornisce un'interfaccia semplificata per lo store auth
 */
export const useAuth = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    checkAuth,
    updateUser,
  } = useAuthStore();

  /**
   * Verifica se l'utente ha un ruolo specifico
   */
  const hasRole = (role: string | string[]) => {
    if (!user) return false;
    
    if (Array.isArray(role)) {
      return role.includes(user.role);
    }
    
    return user.role === role;
  };

  /**
   * Verifica se l'utente è admin
   */
  const isAdmin = () => hasRole('admin');

  /**
   * Verifica se l'utente può accedere a una risorsa
   */
  const canAccess = (requiredRoles?: string[]) => {
    if (!requiredRoles || requiredRoles.length === 0) return true;
    return hasRole(requiredRoles);
  };

  return {
    // Stato
    user,
    isAuthenticated,
    isLoading,
    
    // Azioni
    login,
    register,
    logout,
    checkAuth,
    updateUser,
    
    // Utility
    hasRole,
    isAdmin,
    canAccess,
  };
}; 