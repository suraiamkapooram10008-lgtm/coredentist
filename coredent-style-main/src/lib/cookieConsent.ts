// Cookie Consent Management
// GDPR/CCPA compliant cookie consent

export interface CookiePreferences {
  essential: boolean; // Always true, cannot be disabled
  analytics: boolean;
  marketing: boolean;
}

const COOKIE_CONSENT_KEY = 'cookie_consent';
const COOKIE_PREFERENCES_KEY = 'cookie_preferences';

/**
 * Check if user has given cookie consent
 */
export function hasGivenConsent(): boolean {
  return localStorage.getItem(COOKIE_CONSENT_KEY) === 'true';
}

/**
 * Get user's cookie preferences
 */
export function getCookiePreferences(): CookiePreferences {
  const stored = localStorage.getItem(COOKIE_PREFERENCES_KEY);
  
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      // Invalid JSON, return defaults
    }
  }

  // Default: only essential cookies
  return {
    essential: true,
    analytics: false,
    marketing: false,
  };
}

/**
 * Save cookie preferences
 */
export function saveCookiePreferences(preferences: CookiePreferences): void {
  // Essential cookies always enabled
  const finalPreferences = {
    ...preferences,
    essential: true,
  };

  localStorage.setItem(COOKIE_CONSENT_KEY, 'true');
  localStorage.setItem(COOKIE_PREFERENCES_KEY, JSON.stringify(finalPreferences));

  // Trigger event for other parts of app to react
  window.dispatchEvent(new CustomEvent('cookiePreferencesChanged', {
    detail: finalPreferences,
  }));
}

/**
 * Accept all cookies
 */
export function acceptAllCookies(): void {
  saveCookiePreferences({
    essential: true,
    analytics: true,
    marketing: true,
  });
}

/**
 * Reject non-essential cookies
 */
export function rejectNonEssentialCookies(): void {
  saveCookiePreferences({
    essential: true,
    analytics: false,
    marketing: false,
  });
}

/**
 * Reset cookie consent (for testing or user request)
 */
export function resetCookieConsent(): void {
  localStorage.removeItem(COOKIE_CONSENT_KEY);
  localStorage.removeItem(COOKIE_PREFERENCES_KEY);
  
  window.dispatchEvent(new CustomEvent('cookieConsentReset'));
}

/**
 * Check if specific cookie type is allowed
 */
export function isCookieTypeAllowed(type: keyof CookiePreferences): boolean {
  const preferences = getCookiePreferences();
  return preferences[type];
}
