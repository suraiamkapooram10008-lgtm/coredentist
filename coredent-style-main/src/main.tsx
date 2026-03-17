import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { setupGlobalErrorHandlers } from "./lib/errorHandler";
import { setupSkipLink } from "./lib/accessibility";
import { initWebVitals } from "./lib/webVitals";

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
