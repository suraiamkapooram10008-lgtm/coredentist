import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { setupGlobalErrorHandlers } from "./lib/errorHandler";
import { setupSkipLink } from "./lib/accessibility";
import { initWebVitals } from "./lib/webVitals";
import { logger } from "./lib/logger";

// Setup global error handlers
setupGlobalErrorHandlers();

// Setup accessibility features
setupSkipLink();

// Initialize Web Vitals monitoring
initWebVitals();

// Enable MSW in development mode
async function enableMocking() {
  if (import.meta.env.DEV && import.meta.env.VITE_ENABLE_DEMO_MODE === 'true') {
    const { worker } = await import('./test/mocks/browser');
    return worker.start({
      onUnhandledRequest: 'bypass',
    });
  }
}

enableMocking().then(() => {
  createRoot(document.getElementById("root")!).render(<App />);
});

/**
 * Service Worker Registration
 * Handles offline mode and caching for better performance
 * Moved from App.tsx to main.tsx for better separation of concerns
 */
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((registration) => {
        logger.info("Service worker registered", { scope: registration.scope });
      })
      .catch((error: unknown) => {
        const err = error instanceof Error ? error : new Error(String(error));
        logger.error("Service worker registration failed", err);
      });
  });
}
