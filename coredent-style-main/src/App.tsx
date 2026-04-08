import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { CookieConsent } from "@/components/CookieConsent";
import { PageLoader } from "@/components/ui/spinner";
import { Suspense } from "react";
import { publicRoutes, protectedRoutes, notFoundRoute } from "@/routes/config";

/**
 * RouteGroupErrorBoundary - Wraps route groups with error recovery
 * Provides graceful error handling for specific route categories
 */
function RouteGroupErrorBoundary({
  children,
  fallbackMessage,
}: {
  children: React.ReactNode;
  fallbackMessage: string;
}) {
  return (
    <ErrorBoundary fallback={
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-destructive mb-2">
            {fallbackMessage}
          </h2>
          <p className="text-muted-foreground mb-4">
            Please try refreshing the page or contact support if the problem persists.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:opacity-90"
          >
            Reload Page
          </button>
        </div>
      </div>
    }>
      {children}
    </ErrorBoundary>
  );
}

/**
 * React Query Client Configuration
 * Optimized for medical data with conservative caching
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,     // 5 minutes before data is considered stale
      gcTime: 10 * 60 * 1000,       // 10 minutes garbage collection
      retry: 2,                      // Retry failed requests twice
      refetchOnWindowFocus: false,   // Don't refetch on tab focus (medical data shouldn't change under you)
    },
    mutations: {
      retry: 1,
    },
  },
});

/**
 * Main Application Component
 * 
 * Architecture:
 * - Error boundary wraps entire app for crash recovery
 * - Query client provides server state management
 * - Auth provider handles authentication state
 * - BrowserRouter manages client-side routing
 * - Routes are generated from centralized configuration
 */
const App = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <AuthProvider>
            <Toaster />
            <Sonner />
            <CookieConsent />
            <BrowserRouter>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  {/* Public routes (no authentication required) - wrapped in error boundary */}
                  <Route>
                    {publicRoutes.map((route) => (
                      <Route
                        key={route.path}
                        path={route.path}
                        element={
                          <RouteGroupErrorBoundary fallbackMessage="Unable to load this page">
                            <route.component />
                          </RouteGroupErrorBoundary>
                        }
                      />
                    ))}
                  </Route>

                  {/* Protected routes (authentication required) - wrapped in error boundary */}
                  <Route>
                    {protectedRoutes.map((route) => (
                      <Route
                        key={route.path}
                        path={route.path}
                        element={
                          <RouteGroupErrorBoundary fallbackMessage="Unable to load this section">
                            <ProtectedRoute allowedRoles={route.roles}>
                              <AppShell>
                                <route.component />
                              </AppShell>
                            </ProtectedRoute>
                          </RouteGroupErrorBoundary>
                        }
                      />
                    ))}
                  </Route>

                  {/* 404 route */}
                  <Route path={notFoundRoute.path} element={<notFoundRoute.component />} />

                  {/* Root redirect */}
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </Suspense>
            </BrowserRouter>
          </AuthProvider>
        </TooltipProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;