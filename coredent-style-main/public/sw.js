/**
 * CoreDent PMS Service Worker
 * HIPAA-compliant caching strategy
 * 
 * SECURITY: API responses containing PHI are NEVER cached.
 * Only static assets are cached for offline support.
 */

const CACHE_NAME = 'coredent-static-v2';
const STATIC_CACHE = 'coredent-static-assets-v2';

// Static assets to cache immediately (NO PHI)
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json',
];

// Install event - precache static assets only
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      // Remove old caches
      caches.keys().then((cacheNames) => 
        cacheNames.filter((name) => name !== STATIC_CACHE)
          .map((name) => caches.delete(name))
      ),
      self.clients.claim()
    ])
  );
});

// Fetch event - HIPAA-compliant caching strategy
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // SECURITY: NEVER cache API responses (contain PHI)
  // NetworkOnly strategy for all /api/* requests
  if (url.pathname.startsWith('/api/') || url.pathname.includes('/api/v1/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        // Return generic offline error for API requests
        return new Response(
          JSON.stringify({ error: 'Offline - API unavailable' }),
          { 
            status: 503, 
            headers: { 'Content-Type': 'application/json' }
          }
        );
      })
    );
    return;
  }
  
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip Chrome extension requests
  if (event.request.url.startsWith('chrome-extension://')) return;

  // Cache-first strategy for static assets only (no PHI)
  if (isStaticAsset(url.pathname)) {
    event.respondWith(
      caches.match(event.request)
        .then((cached) => {
          if (cached) return cached;
          return fetch(event.request).then((response) => {
            // Cache successful responses for static assets
            if (response.ok) {
              const clonedResponse = response.clone();
              caches.open(STATIC_CACHE).then((cache) => {
                cache.put(event.request, clonedResponse);
              });
            }
            return response;
          });
        })
    );
    return;
  }

  // Network-only for everything else (no caching)
  event.respondWith(
    fetch(event.request).catch(() => {
      // Return offline page for navigation requests
      if (event.request.mode === 'navigate') {
        return caches.match('/offline.html');
      }
      return undefined;
    })
  );
});

// Helper: Check if request is for static asset (safe to cache)
function isStaticAsset(pathname) {
  const staticExtensions = [
    '.js', '.css', '.html', '.htm',
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
    '.woff', '.woff2', '.ttf', '.eot',
    '.json', '.xml', '.txt', '.pdf'
  ];
  return staticExtensions.some(ext => pathname.endsWith(ext));
}

// Background sync for offline actions (secure - no PHI caching)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-secure-data') {
    event.waitUntil(syncSecureData());
  }
});

// Background sync implementation - queues mutations, not PHI reads
async function syncSecureData() {
  // Get pending mutations from IndexedDB (NOT cached PHI)
  // This would sync with the API when connection is restored
  console.log('[Service Worker] Syncing secure data...');
}

// SECURITY: Clear all caches on message from main thread
self.addEventListener('message', (event) => {
  if (event.data === 'clear-caches') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((name) => caches.delete(name))
        );
      }).then(() => {
        console.log('[Service Worker] All caches cleared');
      })
    );
  }
});