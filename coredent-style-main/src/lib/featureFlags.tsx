// Feature Flags System
// Enables/disables features without code deployment

interface FeatureFlag {
  key: string;
  enabled: boolean;
  description: string;
  rolloutPercentage?: number;
  enabledForRoles?: string[];
  enabledForUsers?: string[];
}

const DEFAULT_FLAGS: Record<string, FeatureFlag> = {
  newDashboard: {
    key: 'newDashboard',
    enabled: false,
    description: 'New dashboard design',
    rolloutPercentage: 0,
  },
  advancedReporting: {
    key: 'advancedReporting',
    enabled: true,
    description: 'Advanced reporting features',
    enabledForRoles: ['owner', 'admin'],
  },
  aiAssistant: {
    key: 'aiAssistant',
    enabled: false,
    description: 'AI-powered clinical assistant',
    rolloutPercentage: 10,
  },
  videoConsultation: {
    key: 'videoConsultation',
    enabled: false,
    description: 'Video consultation feature',
  },
  mobileApp: {
    key: 'mobileApp',
    enabled: true,
    description: 'Mobile app integration',
  },
  automatedReminders: {
    key: 'automatedReminders',
    enabled: true,
    description: 'Automated appointment reminders',
  },
  onlineBooking: {
    key: 'onlineBooking',
    enabled: true,
    description: 'Online appointment booking',
  },
  insuranceVerification: {
    key: 'insuranceVerification',
    enabled: false,
    description: 'Automated insurance verification',
    rolloutPercentage: 25,
  },
};

class FeatureFlagService {
  private flags: Record<string, FeatureFlag> = { ...DEFAULT_FLAGS };
  private userId: string | null = null;
  private userRole: string | null = null;

  /**
   * Initialize feature flags for a user
   */
  initialize(userId: string, userRole: string) {
    this.userId = userId;
    this.userRole = userRole;
    this.loadRemoteFlags();
  }

  /**
   * Check if a feature is enabled
   */
  isEnabled(flagKey: string): boolean {
    const flag = this.flags[flagKey];
    if (!flag) return false;

    // Check if explicitly disabled
    if (!flag.enabled) return false;

    // Check role-based access
    if (flag.enabledForRoles && this.userRole) {
      if (!flag.enabledForRoles.includes(this.userRole)) {
        return false;
      }
    }

    // Check user-specific access
    if (flag.enabledForUsers && this.userId) {
      if (!flag.enabledForUsers.includes(this.userId)) {
        return false;
      }
    }

    // Check rollout percentage
    if (flag.rolloutPercentage !== undefined && this.userId) {
      const userHash = this.hashUserId(this.userId);
      const userPercentage = userHash % 100;
      return userPercentage < flag.rolloutPercentage;
    }

    return true;
  }

  /**
   * Get all enabled flags
   */
  getEnabledFlags(): string[] {
    return Object.keys(this.flags).filter(key => this.isEnabled(key));
  }

  /**
   * Get flag details
   */
  getFlag(flagKey: string): FeatureFlag | null {
    return this.flags[flagKey] || null;
  }

  /**
   * Get all flags
   */
  getAllFlags(): Record<string, FeatureFlag> {
    return { ...this.flags };
  }

  /**
   * Override a flag (for testing/development)
   */
  override(flagKey: string, enabled: boolean) {
    if (this.flags[flagKey]) {
      this.flags[flagKey] = { ...this.flags[flagKey], enabled };
    }
  }

  /**
   * Reset all overrides
   */
  resetOverrides() {
    this.flags = { ...DEFAULT_FLAGS };
  }

  /**
   * Load flags from remote service
   */
  private async loadRemoteFlags() {
    try {
      const response = await fetch('/api/feature-flags', {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const remoteFlags = await response.json();
        this.flags = { ...this.flags, ...remoteFlags };
      }
    } catch (error) {
      // Silently fail and use default flags
      if (import.meta.env.DEV) {
        console.warn('Failed to load remote feature flags, using defaults');
      }
    }
  }

  /**
   * Hash user ID for consistent rollout
   */
  private hashUserId(userId: string): number {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      const char = userId.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }
}

export const featureFlags = new FeatureFlagService();

/**
 * React hook for feature flags
 */
export function useFeatureFlag(flagKey: string): boolean {
  return featureFlags.isEnabled(flagKey);
}

/**
 * React component wrapper for feature flags
 */
interface FeatureGateProps {
  flag: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function FeatureGate({ flag, children, fallback = null }: FeatureGateProps) {
  const isEnabled = useFeatureFlag(flag);
  return isEnabled ? <>{children}</> : <>{fallback}</>;
}
