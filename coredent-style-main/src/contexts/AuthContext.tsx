// ============================================
// CoreDent PMS - Authentication Context
// Manages session state and role-based UI visibility
// Auth logic handled by external backend
// ============================================

import React, { useState, useCallback, useEffect } from 'react';
import type { User, UserRole, LoginCredentials } from '@/types/api';
import { authApi, mfaApi } from '@/services/api';
import { logger } from '@/lib/logger';
import { useToast } from '@/hooks/use-toast';
import { AuthContext, type AuthContextValue, type LoginResult, type PendingMfaChallenge } from '@/contexts/auth-context';
import { refreshCsrfToken, clearCsrfToken } from '@/lib/csrf';
import { analytics, trackLogin, trackLogout } from '@/lib/analytics';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [pendingMfaChallenge, setPendingMfaChallenge] = useState<PendingMfaChallenge | null>(null);
  const { toast } = useToast();

  // effect:audited — Session initialization on mount
  useEffect(() => {
    const checkSession = async () => {
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

  const login = useCallback(async (credentials: LoginCredentials): Promise<LoginResult> => {
    setIsLoading(true);
    setPendingMfaChallenge(null);
    
    try {
      const response = await authApi.login(credentials);
      
      if (response.success && response.data) {
        if ('mfa_required' in response.data && response.data.mfa_required) {
          setPendingMfaChallenge({
            mfaToken: response.data.mfa_token,
            email: response.data.email,
            message: response.data.message,
          });
          return { success: false, mfaRequired: true, message: response.data.message };
        }
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
          return { success: false, message: 'Unable to load user profile' };
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
        
        return { success: true };
      } else {
        toast({
          variant: 'destructive',
          title: 'Login Failed',
          description: response.error?.message || 'Invalid credentials',
        });
        
        return { success: false, message: response.error?.message || 'Invalid credentials' };
      }
    } catch {
      toast({
        variant: 'destructive',
        title: 'Login Error',
        description: 'Unable to connect to server',
      });
      return { success: false, message: 'Unable to connect to server' };
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  const verifyMfa = useCallback(async (totpCode: string, backupCode?: string): Promise<boolean> => {
    if (!pendingMfaChallenge) {
      return false;
    }

    setIsLoading(true);
    try {
      const verifyResponse = await mfaApi.verify({
        mfa_token: pendingMfaChallenge.mfaToken,
        totp_code: totpCode,
        backup_code: backupCode,
      });

      if (!verifyResponse.success || !verifyResponse.data) {
        toast({
          variant: 'destructive',
          title: 'MFA Verification Failed',
          description: verifyResponse.error?.message || 'Invalid verification code',
        });
        return false;
      }

      authApi.setToken(verifyResponse.data.access_token);
      refreshCsrfToken(verifyResponse.data.csrf_token);

      const userResponse = await authApi.getCurrentUser();
      if (!userResponse.success || !userResponse.data) {
        toast({
          variant: 'destructive',
          title: 'Login Failed',
          description: 'Unable to load user profile after MFA',
        });
        clearCsrfToken();
        authApi.setToken(null);
        setPendingMfaChallenge(null);
        return false;
      }

      const resolvedUser = userResponse.data;
      setUser(resolvedUser);
      setPendingMfaChallenge(null);

      analytics.identify(resolvedUser.id, {
        userId: resolvedUser.id,
        email: resolvedUser.email,
        role: resolvedUser.role,
        practiceId: resolvedUser.practiceId,
        practiceName: resolvedUser.practiceName,
      });
      trackLogin(resolvedUser.id, 'mfa');

      toast({
        title: 'Welcome back!',
        description: `Logged in as ${resolvedUser.firstName} ${resolvedUser.lastName}`,
      });
      return true;
    } catch {
      toast({
        variant: 'destructive',
        title: 'MFA Verification Error',
        description: 'Unable to verify MFA code',
      });
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [pendingMfaChallenge, toast]);

  const clearMfaChallenge = useCallback(() => {
    setPendingMfaChallenge(null);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Continue with logout even if API call fails
    }
    
    // CRIT-06 FIX: Clear in-memory tokens only (no localStorage needed)
    authApi.setToken(null);
    setUser(null);
    setPendingMfaChallenge(null);
    
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
    verifyMfa,
    pendingMfaChallenge,
    clearMfaChallenge,
    logout,
    hasRole,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
