import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';

type RateLimitStatus = 'ok' | 'warning' | 'critical';

interface RateLimitInfo {
  remaining: number;
  limit: number;
  resetAt: number;
  status: RateLimitStatus;
}

/**
 * RateLimitFeedback Component
 * Displays API rate limit status from response headers.
 * Shows a subtle warning when approaching limits and a blocking overlay when exceeded.
 * 
 * Reads X-RateLimit-* headers from API responses to track usage.
 */
const RateLimitFeedback: React.FC = () => {
  const [rateLimit, setRateLimit] = useState<RateLimitInfo | null>(null);
  const [show, setShow] = useState(false);

  const updateFromHeaders = useCallback(() => {
    // Intercept fetch to read rate limit headers
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const response = await originalFetch(...args);
      
      const remaining = response.headers.get('X-RateLimit-Remaining');
      const limit = response.headers.get('X-RateLimit-Limit');
      const reset = response.headers.get('X-RateLimit-Reset');
      
      if (remaining && limit) {
        const remainingNum = parseInt(remaining, 10);
        const limitNum = parseInt(limit, 10);
        const resetNum = reset ? parseInt(reset, 10) * 1000 : Date.now() + 60000;
        
        const ratio = remainingNum / limitNum;
        let status: RateLimitStatus = 'ok';
        
        if (ratio <= 0.1) {
          status = 'critical';
        } else if (ratio <= 0.25) {
          status = 'warning';
        }
        
        setRateLimit({
          remaining: remainingNum,
          limit: limitNum,
          resetAt: resetNum,
          status,
        });
        
        // Auto-hide after showing
        if (status !== 'ok') {
          setShow(true);
          setTimeout(() => setShow(false), 8000);
        }
      }
      
      return response;
    };
    
    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  useEffect(() => {
    const cleanup = updateFromHeaders();
    return () => cleanup();
  }, [updateFromHeaders]);

  if (!show || !rateLimit || rateLimit.status === 'ok') return null;

  const getStyles = () => {
    switch (rateLimit.status) {
      case 'critical':
        return {
          bg: 'bg-red-50 dark:bg-red-900/20',
          border: 'border-red-200 dark:border-red-800',
          text: 'text-red-800 dark:text-red-200',
          icon: AlertCircle,
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50 dark:bg-yellow-900/20',
          border: 'border-yellow-200 dark:border-yellow-800',
          text: 'text-yellow-800 dark:text-yellow-200',
          icon: AlertTriangle,
        };
      default:
        return {
          bg: 'bg-blue-50 dark:bg-blue-900/20',
          border: 'border-blue-200 dark:border-blue-800',
          text: 'text-blue-800 dark:text-blue-200',
          icon: Info,
        };
    }
  };

  const styles = getStyles();
  const Icon = styles.icon;
  
  const resetInSeconds = Math.max(0, Math.floor((rateLimit.resetAt - Date.now()) / 1000));
  const minutes = Math.floor(resetInSeconds / 60);
  const seconds = resetInSeconds % 60;

  return (
    <div className={`fixed bottom-4 right-4 z-50 max-w-sm ${styles.bg} ${styles.border} ${styles.text} border rounded-lg shadow-lg p-4`}>
      <div className="flex items-start gap-3">
        <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <p className="text-sm font-medium">
            {rateLimit.status === 'critical' ? 'Rate Limit Nearly Reached' : 'Approaching Rate Limit'}
          </p>
          <p className="text-xs mt-1 opacity-75">
            {rateLimit.remaining} of {rateLimit.limit} requests remaining.
            {resetInSeconds > 0 && ` Resets in ${minutes}m ${seconds}s.`}
          </p>
          {rateLimit.status === 'critical' && (
            <div className="mt-2 w-full bg-red-200 dark:bg-red-800 rounded-full h-1.5">
              <div
                className="bg-red-500 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${(rateLimit.remaining / rateLimit.limit) * 100}%` }}
              />
            </div>
          )}
        </div>
        <button
          onClick={() => setShow(false)}
          className="text-xs opacity-50 hover:opacity-100 flex-shrink-0"
          aria-label="Dismiss"
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default RateLimitFeedback;