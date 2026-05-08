/**
 * Internationalization (i18n) and RTL support
 * L-6 FIX: Foundation for Hindi i18n and RTL layout support
 * 
 * Usage:
 *   import { t, getDirection } from '@/lib/i18n';
 *   <div dir={getDirection()}>{t('dashboard.title')}</div>
 */

export type SupportedLocale = 'en' | 'hi';

interface TranslationDict {
  [key: string]: string | TranslationDict;
}

const translations: Record<SupportedLocale, TranslationDict> = {
  en: {
    common: {
      loading: 'Loading...',
      error: 'An error occurred',
      save: 'Save',
      cancel: 'Cancel',
      delete: 'Delete',
      edit: 'Edit',
      search: 'Search',
      noData: 'No data available',
      retry: 'Retry',
      close: 'Close',
    },
    auth: {
      login: 'Sign in',
      logout: 'Sign out',
      email: 'Email',
      password: 'Password',
      forgotPassword: 'Forgot password?',
      loginFailed: 'Invalid email or password. Please try again.',
    },
    nav: {
      dashboard: 'Dashboard',
      patients: 'Patients',
      schedule: 'Schedule',
      billing: 'Billing',
      settings: 'Settings',
    },
    dashboard: {
      title: 'Dashboard',
      todaysAppointments: "Today's Appointments",
      patientsToday: 'Patients Today',
      pendingCheckouts: 'Pending Checkouts',
      monthlyRevenue: 'Monthly Revenue',
      todaysSchedule: "Today's Schedule",
      recentActivity: 'Recent Activity',
      noAppointments: 'No appointments scheduled',
      noActivity: 'No recent activity',
    },
  },
  hi: {
    common: {
      loading: 'लोड हो रहा है...',
      error: 'एक त्रुटि हुई',
      save: 'सहेजें',
      cancel: 'रद्द करें',
      delete: 'हटाएं',
      edit: 'संपादित करें',
      search: 'खोजें',
      noData: 'कोई डेटा उपलब्ध नहीं',
      retry: 'पुनः प्रयास करें',
      close: 'बंद करें',
    },
    auth: {
      login: 'साइन इन',
      logout: 'साइन आउट',
      email: 'ईमेल',
      password: 'पासवर्ड',
      forgotPassword: 'पासवर्ड भूल गए?',
      loginFailed: 'गलत ईमेल या पासवर्ड। कृपया पुनः प्रयास करें।',
    },
    nav: {
      dashboard: 'डैशबोर्ड',
      patients: 'मरीज',
      schedule: 'अनुसूची',
      billing: 'बिलिंग',
      settings: 'सेटिंग्स',
    },
    dashboard: {
      title: 'डैशबोर्ड',
      todaysAppointments: 'आज के अपॉइंटमेंट',
      patientsToday: 'आज के मरीज',
      pendingCheckouts: 'लंबित चेकआउट',
      monthlyRevenue: 'मासिक राजस्व',
      todaysSchedule: 'आज का कार्यक्रम',
      recentActivity: 'हाल की गतिविधि',
      noAppointments: 'कोई अपॉइंटमेंट निर्धारित नहीं',
      noActivity: 'कोई हालिया गतिविधि नहीं',
    },
  },
};

// RTL locales
const rtlLocales: SupportedLocale[] = [];

/**
 * Get the current locale from localStorage or default to 'en'
 */
export function getLocale(): SupportedLocale {
  if (typeof window === 'undefined') return 'en';
  return (localStorage.getItem('locale') as SupportedLocale) || 'en';
}

/**
 * Set the current locale
 */
export function setLocale(locale: SupportedLocale): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('locale', locale);
  // Update HTML dir attribute for RTL
  document.documentElement.dir = getDirection(locale);
  document.documentElement.lang = locale;
  // Reload to apply translations
  window.location.reload();
}

/**
 * Get the text direction for a locale
 */
export function getDirection(locale?: SupportedLocale): 'ltr' | 'rtl' {
  const currentLocale = locale || getLocale();
  return rtlLocales.includes(currentLocale) ? 'rtl' : 'ltr';
}

/**
 * Simple translation function
 * Supports dot-notation keys: t('dashboard.title')
 */
export function t(key: string, locale?: SupportedLocale): string {
  const currentLocale = locale || getLocale();
  const keys = key.split('.');
  let result: unknown = translations[currentLocale];

  for (const k of keys) {
    if (result && typeof result === 'object' && k in result) {
      result = (result as TranslationDict)[k];
    } else {
      // Fallback to English
      result = translations['en'];
      for (const fallbackKey of keys) {
        if (result && typeof result === 'object' && fallbackKey in result) {
          result = (result as TranslationDict)[fallbackKey];
        } else {
          return key; // Return the key itself if not found
        }
      }
      return typeof result === 'string' ? result : key;
    }
  }

  return typeof result === 'string' ? result : key;
}

/**
 * Initialize i18n on app load
 */
export function initI18n(): void {
  const locale = getLocale();
  document.documentElement.dir = getDirection(locale);
  document.documentElement.lang = locale;
}