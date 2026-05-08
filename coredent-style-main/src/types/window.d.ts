/**
 * Global Window Type Definitions
 * 
 * Extends the global Window interface with third-party library types.
 * This eliminates the need for `as any` casts when accessing global objects.
 */

/**
 * Google Analytics (gtag) interface
 */
interface GtagFunction {
  (command: 'config', targetId: string, config?: Record<string, unknown>): void;
  (command: 'event', eventName: string, eventParams?: Record<string, unknown>): void;
  (command: 'set', config: Record<string, unknown>): void;
  (command: 'get', targetId: string, fieldName: string, callback?: (value: unknown) => void): void;
}

/**
 * PostHog analytics interface
 */
interface PostHogIdentifyOptions {
  [key: string]: unknown;
}

interface PostHogCaptureOptions {
  [key: string]: unknown;
}

interface PostHogInterface {
  identify(userId: string, properties?: PostHogIdentifyOptions): void;
  capture(event: string, properties?: PostHogCaptureOptions): void;
  reset(): void;
  opt_in_capturing(): void;
  opt_out_capturing(): void;
  has_opted_in_capturing(): boolean;
  has_opted_out_capturing(): boolean;
  get_distinct_id(): string;
  get_session_id(): string;
}

/**
 * Razorpay payment gateway interface
 */
interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name?: string;
  description?: string;
  image?: string;
  order_id?: string;
  customer_id?: string;
  email?: string;
  contact?: string;
  notes?: Record<string, unknown>;
  theme?: {
    color?: string;
  };
  prefill?: {
    name?: string;
    email?: string;
    contact?: string;
  };
  handler?: (response: RazorpayResponse) => void;
  modal?: {
    ondismiss?: () => void;
    onclosed?: () => void;
  };
  recurring?: string;
  subscription_notify?: number;
  expire_at?: number;
  expire_by?: number;
  receipt?: string;
  first_min_partial_amount?: number;
  reference_id?: string;
  description_prefix?: string;
}

interface RazorpayResponse {
  razorpay_payment_id: string;
  razorpay_order_id?: string;
  razorpay_signature?: string;
}

interface RazorpayInstance {
  open(): void;
  close(): void;
}

interface RazorpayConstructor {
  new (options: RazorpayOptions): RazorpayInstance;
}

interface RazorpayWindow {
  Razorpay: RazorpayConstructor;
}

/**
 * Stripe payment gateway interface
 */
interface StripeElement {
  mount(selector: string): void;
  unmount(): void;
  on(event: string, handler: (event: unknown) => void): void;
  update(options: Record<string, unknown>): void;
}

interface StripeElements {
  create(type: string, options?: Record<string, unknown>): StripeElement;
}

interface StripeInstance {
  elements(): StripeElements;
  confirmCardPayment(clientSecret: string, options?: Record<string, unknown>): Promise<unknown>;
  confirmCardSetup(clientSecret: string, options?: Record<string, unknown>): Promise<unknown>;
}

interface StripeConstructor {
  (publicKey: string): StripeInstance;
}

/**
 * Mixpanel analytics interface
 */
interface MixpanelTrackOptions {
  [key: string]: unknown;
}

interface MixpanelInterface {
  track(event: string, properties?: MixpanelTrackOptions): void;
  identify(userId: string): void;
  people: {
    set(properties: Record<string, unknown>): void;
    increment(property: string, value?: number): void;
  };
  register(properties: Record<string, unknown>): void;
  unregister(property: string): void;
  reset(): void;
}

/**
 * Sentry error tracking interface
 */
interface SentryOptions {
  dsn?: string;
  environment?: string;
  release?: string;
  tracesSampleRate?: number;
  integrations?: unknown[];
  beforeSend?: (event: unknown, hint: unknown) => unknown;
}

interface SentryInterface {
  init(options: SentryOptions): void;
  captureException(error: Error): void;
  captureMessage(message: string, level?: string): void;
  setUser(user: Record<string, unknown> | null): void;
  setTag(key: string, value: string): void;
  setContext(name: string, context: Record<string, unknown>): void;
}

/**
 * Extend the global Window interface
 */
declare global {
  interface Window {
    /**
     * Google Analytics (gtag) function
     * @example window.gtag?.('event', 'page_view')
     */
    gtag?: GtagFunction;

    /**
     * PostHog analytics
     * @example window.posthog?.identify('user-123')
     */
    posthog?: PostHogInterface;

    /**
     * Razorpay payment gateway
     * @example new window.Razorpay?.(options)
     */
    Razorpay?: RazorpayConstructor;

    /**
     * Stripe payment gateway
     * @example window.Stripe?.('pk_test_...')
     */
    Stripe?: StripeConstructor;

    /**
     * Mixpanel analytics
     * @example window.mixpanel?.track('event')
     */
    mixpanel?: MixpanelInterface;

    /**
     * Sentry error tracking
     * @example window.Sentry?.captureException(error)
     */
    Sentry?: SentryInterface;

    /**
     * Development bypass flag (development only)
     * @internal
     */
    DEV_BYPASS_AUTH?: boolean;

    /**
     * Custom application data
     * @internal
     */
    __APP_CONFIG__?: Record<string, unknown>;

    /**
     * Service worker registration
     */
    __SW_REGISTRATION__?: ServiceWorkerRegistration;
  }
}

export {};
