/**
 * Utility Type Definitions
 * Generic utility types for improved type constraints
 */

// ============================================
// Function Types
// ============================================

/**
 * Generic function type with proper constraints
 * Replaces (...args: any[]) => any pattern
 */
export type GenericFunction<TArgs extends unknown[] = unknown[], TReturn = unknown> = (
  ...args: TArgs
) => TReturn;

/**
 * Async function type with proper constraints
 * Replaces (...args: any[]) => Promise<any> pattern
 */
export type AsyncFunction<TArgs extends unknown[] = unknown[], TReturn = unknown> = (
  ...args: TArgs
) => Promise<TReturn>;

/**
 * Debounced function type
 * Function that has been debounced
 */
export type DebouncedFunction<TArgs extends unknown[] = unknown[], TReturn = unknown> = (
  ...args: TArgs
) => void;

/**
 * Throttled function type
 * Function that has been throttled
 */
export type ThrottledFunction<TArgs extends unknown[] = unknown[], TReturn = unknown> = (
  ...args: TArgs
) => TReturn | void;

/**
 * Cached function type
 * Function that has been cached
 */
export type CachedFunction<TArgs extends unknown[] = unknown[], TReturn = unknown> = (
  ...args: TArgs
) => TReturn;

// ============================================
// Formatter Types
// ============================================

/**
 * Value formatter function
 * Formats a value for display
 */
export type ValueFormatter<T = unknown> = (value: T) => string;

/**
 * Number formatter
 * Formats numbers for display
 */
export type NumberFormatter = ValueFormatter<number>;

/**
 * String formatter
 * Formats strings for display
 */
export type StringFormatter = ValueFormatter<string>;

/**
 * Date formatter
 * Formats dates for display
 */
export type DateFormatter = ValueFormatter<Date>;

// ============================================
// Callback Types
// ============================================

/**
 * Generic callback function
 * Callback with typed parameter
 */
export type Callback<T = void> = (value: T) => void;

/**
 * Generic async callback
 * Async callback with typed parameter
 */
export type AsyncCallback<T = void> = (value: T) => Promise<void>;

/**
 * Event handler callback
 * Handles events with typed event object
 */
export type EventHandler<E extends Event = Event> = (event: E) => void;

/**
 * Change handler callback
 * Handles change events
 */
export type ChangeHandler<T = unknown> = (value: T) => void;

/**
 * Submit handler callback
 * Handles form submission
 */
export type SubmitHandler<T = unknown> = (data: T) => void | Promise<void>;

// ============================================
// Predicate Types
// ============================================

/**
 * Type predicate function
 * Checks if value matches a type
 */
export type TypePredicate<T> = (value: unknown): value is T;

/**
 * Generic predicate function
 * Checks if value matches a condition
 */
export type Predicate<T = unknown> = (value: T) => boolean;

/**
 * Async predicate function
 * Async check if value matches a condition
 */
export type AsyncPredicate<T = unknown> = (value: T) => Promise<boolean>;

// ============================================
// Mapper Types
// ============================================

/**
 * Generic mapper function
 * Maps value from one type to another
 */
export type Mapper<TFrom = unknown, TTo = unknown> = (value: TFrom) => TTo;

/**
 * Async mapper function
 * Async maps value from one type to another
 */
export type AsyncMapper<TFrom = unknown, TTo = unknown> = (value: TFrom) => Promise<TTo>;

/**
 * Array mapper function
 * Maps array items
 */
export type ArrayMapper<T = unknown, R = unknown> = (item: T, index: number, array: T[]) => R;

// ============================================
// Comparator Types
// ============================================

/**
 * Comparator function
 * Compares two values
 */
export type Comparator<T = unknown> = (a: T, b: T) => number;

/**
 * Equality checker
 * Checks if two values are equal
 */
export type EqualityChecker<T = unknown> = (a: T, b: T) => boolean;

// ============================================
// Constructor Types
// ============================================

/**
 * Constructor function
 * Creates instances of a type
 */
export type Constructor<T = unknown> = new (...args: unknown[]) => T;

/**
 * Factory function
 * Creates instances without new keyword
 */
export type Factory<T = unknown> = (...args: unknown[]) => T;

// ============================================
// Constraint Types
// ============================================

/**
 * Keyed object constraint
 * Ensures object has string keys
 */
export type KeyedObject = Record<string, unknown>;

/**
 * Indexable constraint
 * Ensures value can be indexed
 */
export type Indexable<T = unknown> = {
  [key: string]: T;
};

/**
 * Nullable constraint
 * Value can be null or undefined
 */
export type Nullable<T> = T | null | undefined;

/**
 * Optional constraint
 * Value can be undefined
 */
export type Optional<T> = T | undefined;

/**
 * Readonly constraint
 * Makes all properties readonly
 */
export type Readonly<T> = {
  readonly [K in keyof T]: T[K];
};

/**
 * Partial constraint
 * Makes all properties optional
 */
export type Partial<T> = {
  [K in keyof T]?: T[K];
};

/**
 * Required constraint
 * Makes all properties required
 */
export type Required<T> = {
  [K in keyof T]-?: T[K];
};

/**
 * Pick constraint
 * Selects specific properties
 */
export type Pick<T, K extends keyof T> = {
  [P in K]: T[P];
};

/**
 * Omit constraint
 * Excludes specific properties
 */
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;

/**
 * Record constraint
 * Creates object with specific keys and values
 */
export type Record<K extends string | number | symbol, T> = {
  [P in K]: T;
};
