// Internationalization utilities for multi-language support

type Translations = Record<string, Record<string, string>>;

interface I18nConfig {
  defaultLocale: string;
  supportedLocales: string[];
  translations: Translations;
}

class I18n {
  private currentLocale: string;
  private defaultLocale: string;
  private supportedLocales: string[];
  private translations: Translations;

  constructor(config: I18nConfig) {
    this.defaultLocale = config.defaultLocale;
    this.supportedLocales = config.supportedLocales;
    this.translations = config.translations;
    
    // Try to get locale from localStorage or browser
    const savedLocale = localStorage.getItem('locale');
    const browserLocale = navigator.language.split('-')[0];
    
    this.currentLocale = 
      savedLocale && this.supportedLocales.includes(savedLocale)
        ? savedLocale
        : this.supportedLocales.includes(browserLocale)
        ? browserLocale
        : this.defaultLocale;
  }

  t(key: string, params?: Record<string, string | number>): string {
    const keys = key.split('.');
    let translation: any = this.translations[this.currentLocale];

    // Navigate through nested keys
    for (const k of keys) {
      if (translation && typeof translation === 'object') {
        translation = translation[k];
      } else {
        translation = undefined;
        break;
      }
    }

    // Fallback to default locale
    if (!translation) {
      translation = this.translations[this.defaultLocale];
      for (const k of keys) {
        if (translation && typeof translation === 'object') {
          translation = translation[k];
        } else {
          translation = key; // Return key if not found
          break;
        }
      }
    }

    // Replace parameters
    if (params && typeof translation === 'string') {
      Object.entries(params).forEach(([param, value]) => {
        translation = translation.replace(`{{${param}}}`, String(value));
      });
    }

    return translation || key;
  }

  setLocale(locale: string): void {
    if (this.supportedLocales.includes(locale)) {
      this.currentLocale = locale;
      localStorage.setItem('locale', locale);
      document.documentElement.lang = locale;
      
      // Dispatch event for components to react
      window.dispatchEvent(new CustomEvent('localechange', { detail: { locale } }));
    }
  }

  getLocale(): string {
    return this.currentLocale;
  }

  getSupportedLocales(): string[] {
    return this.supportedLocales;
  }

  addTranslations(locale: string, translations: Record<string, any>): void {
    if (!this.translations[locale]) {
      this.translations[locale] = {};
    }
    this.translations[locale] = { ...this.translations[locale], ...translations };
  }
}

// Default translations
const translations: Translations = {
  en: {
    common: {
      save: 'Save',
      cancel: 'Cancel',
      delete: 'Delete',
      edit: 'Edit',
      add: 'Add',
      search: 'Search',
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      confirm: 'Confirm',
      back: 'Back',
      next: 'Next',
      previous: 'Previous',
      close: 'Close',
    },
    auth: {
      login: 'Sign In',
      logout: 'Sign Out',
      email: 'Email',
      password: 'Password',
      forgotPassword: 'Forgot Password?',
      rememberMe: 'Remember Me',
      loginError: 'Invalid email or password',
      sessionExpired: 'Your session has expired. Please sign in again.',
    },
    dashboard: {
      title: 'Dashboard',
      welcome: 'Welcome back, {{name}}!',
      todayAppointments: "Today's Appointments",
      upcomingAppointments: 'Upcoming Appointments',
      recentPatients: 'Recent Patients',
    },
    patients: {
      title: 'Patients',
      addPatient: 'Add Patient',
      editPatient: 'Edit Patient',
      deletePatient: 'Delete Patient',
      patientDetails: 'Patient Details',
      firstName: 'First Name',
      lastName: 'Last Name',
      dateOfBirth: 'Date of Birth',
      phone: 'Phone',
      email: 'Email',
      address: 'Address',
      status: 'Status',
      active: 'Active',
      inactive: 'Inactive',
    },
    appointments: {
      title: 'Appointments',
      schedule: 'Schedule',
      newAppointment: 'New Appointment',
      editAppointment: 'Edit Appointment',
      cancelAppointment: 'Cancel Appointment',
      patient: 'Patient',
      provider: 'Provider',
      date: 'Date',
      time: 'Time',
      duration: 'Duration',
      type: 'Type',
      status: 'Status',
      notes: 'Notes',
    },
    billing: {
      title: 'Billing',
      invoices: 'Invoices',
      payments: 'Payments',
      createInvoice: 'Create Invoice',
      invoiceNumber: 'Invoice Number',
      amount: 'Amount',
      dueDate: 'Due Date',
      paid: 'Paid',
      unpaid: 'Unpaid',
      overdue: 'Overdue',
    },
    settings: {
      title: 'Settings',
      general: 'General',
      profile: 'Profile',
      security: 'Security',
      notifications: 'Notifications',
      language: 'Language',
      theme: 'Theme',
      saveChanges: 'Save Changes',
    },
    errors: {
      notFound: 'Page not found',
      serverError: 'Server error occurred',
      networkError: 'Network error. Please check your connection.',
      unauthorized: 'You are not authorized to access this resource',
      validationError: 'Please check your input and try again',
    },
  },
  es: {
    common: {
      save: 'Guardar',
      cancel: 'Cancelar',
      delete: 'Eliminar',
      edit: 'Editar',
      add: 'Agregar',
      search: 'Buscar',
      loading: 'Cargando...',
      error: 'Error',
      success: 'Éxito',
      confirm: 'Confirmar',
      back: 'Atrás',
      next: 'Siguiente',
      previous: 'Anterior',
      close: 'Cerrar',
    },
    auth: {
      login: 'Iniciar Sesión',
      logout: 'Cerrar Sesión',
      email: 'Correo Electrónico',
      password: 'Contraseña',
      forgotPassword: '¿Olvidaste tu contraseña?',
      rememberMe: 'Recuérdame',
      loginError: 'Correo o contraseña inválidos',
      sessionExpired: 'Tu sesión ha expirado. Por favor inicia sesión nuevamente.',
    },
    dashboard: {
      title: 'Panel de Control',
      welcome: '¡Bienvenido de nuevo, {{name}}!',
      todayAppointments: 'Citas de Hoy',
      upcomingAppointments: 'Próximas Citas',
      recentPatients: 'Pacientes Recientes',
    },
    patients: {
      title: 'Pacientes',
      addPatient: 'Agregar Paciente',
      editPatient: 'Editar Paciente',
      deletePatient: 'Eliminar Paciente',
      patientDetails: 'Detalles del Paciente',
      firstName: 'Nombre',
      lastName: 'Apellido',
      dateOfBirth: 'Fecha de Nacimiento',
      phone: 'Teléfono',
      email: 'Correo',
      address: 'Dirección',
      status: 'Estado',
      active: 'Activo',
      inactive: 'Inactivo',
    },
  },
};

// Create global i18n instance
export const i18n = new I18n({
  defaultLocale: 'en',
  supportedLocales: ['en', 'es'],
  translations,
});

// React hook for i18n
export function useTranslation() {
  const [locale, setLocale] = React.useState(i18n.getLocale());

  React.useEffect(() => {
    const handleLocaleChange = (event: CustomEvent) => {
      setLocale(event.detail.locale);
    };

    window.addEventListener('localechange', handleLocaleChange as EventListener);
    return () => {
      window.removeEventListener('localechange', handleLocaleChange as EventListener);
    };
  }, []);

  return {
    t: (key: string, params?: Record<string, string | number>) => i18n.t(key, params),
    locale,
    setLocale: (newLocale: string) => i18n.setLocale(newLocale),
    supportedLocales: i18n.getSupportedLocales(),
  };
}

// Add React import for the hook
import React from 'react';
