/**
 * State Type Definitions
 * Centralized types for React state management
 */

// ============================================
// Generic State Types
// ============================================

/**
 * Async operation state
 * Tracks loading, error, and data states
 */
export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

/**
 * Paginated state
 * Tracks paginated data with metadata
 */
export interface PaginatedState<T> {
  items: T[];
  page: number;
  limit: number;
  total: number;
  loading: boolean;
  error: Error | null;
}

/**
 * Form state
 * Tracks form submission and validation
 */
export interface FormStateType {
  isSubmitting: boolean;
  isValid: boolean;
  isDirty: boolean;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
}

/**
 * Modal state
 * Tracks modal open/close state
 */
export interface ModalState {
  isOpen: boolean;
  data?: unknown;
}

/**
 * Filter state
 * Tracks filter selections
 */
export interface FilterState {
  [key: string]: string | number | boolean | string[] | null;
}

/**
 * Sort state
 * Tracks sorting configuration
 */
export interface SortState {
  field: string;
  direction: 'asc' | 'desc';
}

/**
 * Selection state
 * Tracks selected items
 */
export interface SelectionState<T> {
  selected: T | null;
  selectedIds: string[];
  isMultiple: boolean;
}

// ============================================
// Booking State Types
// ============================================

/**
 * Appointment type selection
 * Used in booking flow
 */
export interface AppointmentTypeSelection {
  id: string;
  name: string;
  duration: number;
  description?: string;
}

/**
 * Booking form state
 * Tracks booking form data
 */
export interface BookingFormState {
  selectedType: AppointmentTypeSelection | null;
  selectedDate: Date;
  selectedSlot: string | null;
  formData: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    reason: string;
    isNewPatient: boolean;
  };
}

// ============================================
// Chart State Types
// ============================================

/**
 * Chart formatter function
 * Formats chart values for display
 */
export type ChartFormatter = (value: number | string) => string;

/**
 * Chart data point
 * Represents a single data point in a chart
 */
export interface ChartDataPoint {
  [key: string]: string | number | Date;
}

/**
 * Chart state
 * Tracks chart configuration and data
 */
export interface ChartState {
  data: ChartDataPoint[];
  loading: boolean;
  error: Error | null;
  formatter?: ChartFormatter;
}

// ============================================
// UI State Types
// ============================================

/**
 * Notification state
 * Tracks notification display
 */
export interface NotificationState {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

/**
 * Sidebar state
 * Tracks sidebar open/close
 */
export interface SidebarState {
  isOpen: boolean;
  isCollapsed: boolean;
}

/**
 * Theme state
 * Tracks theme preference
 */
export interface ThemeState {
  mode: 'light' | 'dark' | 'system';
  primaryColor?: string;
}

// ============================================
// Utility Types
// ============================================

/**
 * State setter function
 * Generic state setter type
 */
export type StateSetter<T> = (value: T | ((prev: T) => T)) => void;

/**
 * State initializer function
 * Function that initializes state
 */
export type StateInitializer<T> = () => T;

/**
 * State reducer
 * Reducer function for complex state
 */
export type StateReducer<S, A> = (state: S, action: A) => S;

/**
 * State action
 * Generic action type for reducers
 */
export interface StateAction<T = string, P = unknown> {
  type: T;
  payload?: P;
}
