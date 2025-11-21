// Versioned cache name for easy invalidation
const CACHE_VERSION = 'v1';
const PRECACHE = `aft-precache-${CACHE_VERSION}`;
const RUNTIME = `aft-runtime-${CACHE_VERSION}`;

// Core resources to precache (minimal – extend later)
const PRECACHE_URLS = [
  '/',
  '/status',
  '/weather',
  '/sea-temp-test',
  '/offline',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(PRECACHE).then(cache => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => ![PRECACHE, RUNTIME].includes(k)).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

// Utility: determine if request is a navigation
function isNavigationRequest(request) {
  return request.mode === 'navigate';
}

self.addEventListener('fetch', event => {
  const { request } = event;

  // Skip non-GET
  if (request.method !== 'GET') return;

  // Navigation requests: Network first, fallback to offline page
  if (isNavigationRequest(request)) {
    event.respondWith(
      fetch(request).catch(() => caches.open(PRECACHE).then(c => c.match('/offline')))
    );
    return;
  }

  const url = new URL(request.url);

  // Same-origin static: Cache-first
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return caches.open(RUNTIME).then(cache =>
          fetch(request).then(response => {
            // Only cache successful basic responses
            if (response && response.status === 200 && response.type === 'basic') {
              cache.put(request, response.clone());
            }
            return response;
          })
        );
      })
    );
    return;
  }

  // Cross-origin (e.g., badatime iframe) – just try network; no cache
  event.respondWith(fetch(request));
});
