// Analytics Integration
// PostHog for product analytics

import { logger } from './logger';

interface PostHogWindow extends Window {
  posthog?: {
    identify: (userId: string, properties: Record<string, unknown>) => void;
    capture: (event: string, properties?: Record<string, unknown>) => void;
    reset: () => void;
    people: {
      set: (properties: Record<string, unknown>) => void;
    };
  };
}

interface AnalyticsEvent {
  event: string;
  properties?: Record<string, unknown>;
}

interface UserProperties {
  userId?: string;
  email?: string;
  role?: string;
  practiceId?: string;
  practiceName?: string;
  [key: string]: unknown;
}

class Analytics {
  private enabled: boolean;
  private userId: string | null = null;

  constructor() {
    this.enabled = !import.meta.env.DEV && import.meta.env.VITE_ANALYTICS_ENABLED === 'true';
  }

  /**
   * Initialize analytics with user information
   */
  identify(userId: string, properties: UserProperties = {}) {
    if (!this.enabled) return;

    this.userId = userId;

    // PostHog identify
    const w = window as unknown as PostHogWindow;
    if (typeof window !== 'undefined' && w.posthog) {
      w.posthog.identify(userId, properties);
    }
  }

  /**
   * Track an event
   */
  track(event: string, properties: Record<string, unknown> = {}) {
    if (!this.enabled) return;

    const eventData: AnalyticsEvent = {
      event,
      properties: {
        ...properties,
        timestamp: new Date().toISOString(),
        userId: this.userId,
      },
    };

    // PostHog track
    const w = window as unknown as PostHogWindow;
    if (typeof window !== 'undefined' && w.posthog) {
      w.posthog.capture(event, eventData.properties);
    }

    // Log in development only
    if (import.meta.env.DEV) {
      logger.debug('[Analytics]', { event, properties: eventData.properties });
    }
  }

  /**
   * Track page view
   */
  page(pageName: string, properties: Record<string, unknown> = {}) {
    this.track('Page Viewed', {
      page: pageName,
      ...properties,
    });
  }

  /**
   * Reset analytics (on logout)
   */
  reset() {
    this.userId = null;

    const w = window as unknown as PostHogWindow;
    if (typeof window !== 'undefined' && w.posthog) {
      w.posthog.reset();
    }
  }

  /**
   * Set user properties
   */
  setUserProperties(properties: UserProperties) {
    if (!this.enabled) return;

    const w = window as unknown as PostHogWindow;
    if (typeof window !== 'undefined' && w.posthog) {
      w.posthog.people.set(properties);
    }
  }

  /**
   * Track feature usage
   */
  trackFeature(featureName: string, action: string, properties: Record<string, unknown> = {}) {
    this.track(`Feature: ${featureName}`, {
      action,
      ...properties,
    });
  }
}

export const analytics = new Analytics();

// Common event tracking functions

export const trackSignup = (userId: string, method: string) => {
  analytics.track('User Signed Up', { method });
};

export const trackLogin = (userId: string, method: string) => {
  analytics.track('User Logged In', { method });
};

export const trackLogout = () => {
  analytics.track('User Logged Out', {});
  analytics.reset();
};

export const trackPatientCreated = (patientId: string) => {
  analytics.track('Patient Created', { patientId });
};

export const trackAppointmentBooked = (appointmentId: string, type: string) => {
  analytics.track('Appointment Booked', { appointmentId, type });
};

export const trackInvoiceCreated = (invoiceId: string, amount: number) => {
  analytics.track('Invoice Created', { invoiceId, amount });
};

export const trackPaymentReceived = (paymentId: string, amount: number, method: string) => {
  analytics.track('Payment Received', { paymentId, amount, method });
};

export const trackFeatureUsed = (feature: string, action: string) => {
  analytics.trackFeature(feature, action);
};

export const trackError = (error: Error, context?: Record<string, unknown>) => {
  analytics.track('Error Occurred', {
    error: error.message,
    stack: error.stack,
    ...context,
  });
};

export const trackPerformance = (metric: string, value: number) => {
  analytics.track('Performance Metric', {
    metric,
    value,
  });
};
