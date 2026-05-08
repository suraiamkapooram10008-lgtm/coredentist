// ============================================
// CoreDent PMS - Authentication Context
// Manages session state and role-based UI visibility
// Auth logic handled by external backend
// ============================================

import React, { useState, useCallback, useEffect } from 'react';
import type { User, UserRole, LoginCredentials } from '@/types/api';
import { authApi } from '@/services/api';
import { logger } from '@/lib/logger';
import { useToast } from '@/hooks/use-toast';
import { AuthContext, type AuthContextValue } from '@/contexts/auth-context';
import { refreshCsrfToken, clearCsrfToken } from '@/lib/csrf';
import { analytics, trackLogin, trackLogout } from '@/lib/analytics';

  // Development mode bypass - ONLY works in development builds, NEVER in production
  const DEV_MODE = import.meta.env.MODE === 'development';
  const DEV_BYPASS_AUTH = import.meta.env.MODE === 'development' && import.meta.env.VITE_DEV_BYPASS_AUTH === 'true';
  
  // Production safety check - this will throw if somehow bypass is enabled in production
  if (typeof window !== 'undefined' && import.meta.env.MODE === 'production' && import.meta.env.VITE_DEV_BYPASS_AUTH === 'true') {
    logger.error('SECURITY ERROR: Auth bypass cannot be enabled in production!');
    throw new Error('Auth bypass enabled in production - this is a security violation');
  }

const DEV_USER: User = {
  id: 'dev-user-1',
  email: 'dev@coredent.com',
  firstName: 'Dev',
  lastName: 'User',
  role: 'owner',
  practiceId: 'dev-practice-1',
  practiceName: 'Development Practice',
  practiceCountry: 'US',
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();
  
  // CRITICAL FIX: Token storage for cross-origin auth

  // effect:audited — Session initialization on mount
  useEffect(() => {
    const checkSession = async () => {
      // Development mode bypass - ONLY works in development build mode
      if (DEV_MODE && DEV_BYPASS_AUTH) {
        logger.debug('Development Mode: Authentication bypassed (dev build only)');
        logger.debug(`Logged in as: ${DEV_USER.email}`);
        setUser(DEV_USER);
        setIsLoading(false);
        return;
      }

      // CRIT-06 FIX: No localStorage token storage - use in-memory only
      // Tokens are obtained from response body on login and stored in ApiClient memory
      // On page reload, user must re-login (more secure for HIPAA compliance)
      logger.debug('Session check: No persistent token storage (HIPAA compliant)');

      // Call API to verify session - cookies will be sent automatically
      try {
        const response = await authApi.getCurrentUser();
        
        if (response.success && response.data) {
          setUser(response.data);
        } else {
      // Session invalid - clear session
      clearCsrfToken();
      authApi.setToken(null);
      setUser(null);
        }
      } catch {
        // Session check failed - treat as logged out
        clearCsrfToken();
        authApi.setToken(null);
      }
      
      setIsLoading(false);
    };

    checkSession();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      const response = await authApi.login(credentials);
      
      if (response.success && response.data) {
        const { csrf_token, access_token } = response.data;
        
        // CRIT-06 FIX: Store token in ApiClient memory ONLY (NOT localStorage)
        // This prevents XSS attacks from stealing tokens via localStorage access
        if (access_token) {
          authApi.setToken(access_token);
          // NO localStorage.setItem - removed for HIPAA compliance
        }
        
        // Store CSRF token for request headers
        refreshCsrfToken(csrf_token);

        const userResponse = await authApi.getCurrentUser();
        if (!userResponse.success || !userResponse.data) {
          clearCsrfToken();
          authApi.setToken(null);
          // NO localStorage.removeItem needed - not stored anymore
          toast({
            variant: 'destructive',
            title: 'Login Failed',
            description: 'Unable to load user profile',
          });
          return false;
        }

        const user = userResponse.data;
        setUser(user);

        analytics.identify(user.id, {
          userId: user.id,
          email: user.email,
          role: user.role,
          practiceId: user.practiceId,
          practiceName: user.practiceName,
        });
        trackLogin(user.id, 'email');
        
        toast({
          title: 'Welcome back!',
          description: `Logged in as ${user.firstName} ${user.lastName}`,
        });
        
        return true;
      } else {
        toast({
          variant: 'destructive',
          title: 'Login Failed',
          description: response.error?.message || 'Invalid credentials',
        });
        
        return false;
      }
    } catch {
      toast({
        variant: 'destructive',
        title: 'Login Error',
        description: 'Unable to connect to server',
      });
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Continue with logout even if API call fails
    }
    
    // CRIT-06 FIX: Clear in-memory tokens only (no localStorage needed)
    authApi.setToken(null);
    setUser(null);
    
    // Clear CSRF token on logout
    clearCsrfToken();
    
    // Track logout event
    trackLogout();
    
    toast({
      title: 'Logged out',
      description: 'You have been signed out',
    });
  }, [toast]);

  const hasRole = useCallback((...roles: UserRole[]): boolean => {
    if (!user) return false;
    return roles.includes(user.role);
  }, [user]);

  const value: AuthContextValue = {
    user,
    isAuthenticated: !!user,
    isLoading,
    role: user?.role || null,
    login,
    logout,
    hasRole,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
