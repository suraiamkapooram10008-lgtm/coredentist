import { createContext, useContext } from 'react';
import type { User, UserRole, LoginCredentials } from '@/types/api';

export interface PendingMfaChallenge {
  mfaToken: string;
  email: string;
  message: string;
}

export interface LoginResult {
  success: boolean;
  mfaRequired?: boolean;
  message?: string;
}

export interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  role: UserRole | null;
  login: (credentials: LoginCredentials) => Promise<LoginResult>;
  verifyMfa: (totpCode: string, backupCode?: string) => Promise<boolean>;
  pendingMfaChallenge: PendingMfaChallenge | null;
  clearMfaChallenge: () => void;
  logout: () => Promise<void>;
  hasRole: (...roles: UserRole[]) => boolean;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
