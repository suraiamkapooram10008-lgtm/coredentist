// ============================================
// CoreDent PMS - MSW Browser Setup
// Mock Service Worker browser configuration
// ============================================

import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

// Create the MSW worker with our handlers
export const worker = setupWorker(...handlers);
