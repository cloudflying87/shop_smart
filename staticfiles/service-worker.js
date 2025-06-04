/**
 * Service Worker for ShopSmart
 * Provides offline functionality and caching
 */

// Cache names - incrementing versions forces cache refresh on updates
const CACHE_VERSION = 'v4';
const STATIC_CACHE = `shopsmart-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `shopsmart-dynamic-${CACHE_VERSION}`;
const API_CACHE = `shopsmart-api-${CACHE_VERSION}`;
const IMAGE_CACHE = `shopsmart-images-${CACHE_VERSION}`;

// Resources to cache immediately on install
const STATIC_ASSETS = [
  '/', 
  '/app/',
  '/app/offline/',
  '/static/css/base.css',
  '/static/css/mobile.css',
  '/static/css/shopping-list.css',
  '/static/css/products.css',
  '/static/js/app.js',
  '/static/js/modal-handler.js',
  '/static/js/theme-manager.js',
  '/static/js/mobile-nav.js',
  '/static/js/shopping-list.js',
  '/static/js/location-changer.js',
  '/static/js/offline-data-manager.js',
  '/static/js/service-worker-register.js',
  '/static/manifest.json',
  '/static/icons/logo.svg',
  '/static/icons/favicon.ico',
  '/static/icons/icon-72x72.png',
  '/static/icons/icon-96x96.png',
  '/static/icons/icon-128x128.png',
  '/static/icons/icon-144x144.png',
  '/static/icons/icon-152x152.png',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-384x384.png',
  '/static/icons/icon-512x512.png'
];

// Maximum number of items in dynamic cache
const DYNAMIC_CACHE_LIMIT = 100;
const IMAGE_CACHE_LIMIT = 50;
const API_CACHE_LIMIT = 30;

// Network timeout in milliseconds
const NETWORK_TIMEOUT = 5000;

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker: Installing new version');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        // Pre-cache static assets
        console.log('Service Worker: Caching static assets', STATIC_ASSETS);
        return cache.addAll(STATIC_ASSETS)
          .catch(error => {
            console.error('Service Worker: Cache addAll error', error);
            // Try caching assets one by one to identify the problematic one
            const cachePromises = STATIC_ASSETS.map(url => {
              return cache.add(url).catch(err => {
                console.error(`Failed to cache asset: ${url}`, err);
                return Promise.resolve(); // Continue despite error
              });
            });
            return Promise.all(cachePromises);
          });
      })
      .then(() => {
        // Skip waiting to activate immediately
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  const currentCaches = [STATIC_CACHE, DYNAMIC_CACHE, API_CACHE, IMAGE_CACHE];

  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        // Remove any old caches not in currentCaches
        return Promise.all(
          cacheNames.map(cacheName => {
            if (!currentCaches.includes(cacheName)) {
              console.log('Service Worker: Removing old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        // Claim clients to ensure updates take effect immediately
        return self.clients.claim();
      })
  );
});

// Helper function to limit cache size
async function trimCache(cacheName, maxItems) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  
  if (keys.length > maxItems) {
    // Remove oldest items if cache exceeds limit
    const deletePromises = keys.slice(0, keys.length - maxItems).map(key => cache.delete(key));
    await Promise.all(deletePromises);
  }
}

// Network timeout wrapper
function fetchWithTimeout(request, timeout = NETWORK_TIMEOUT) {
  return Promise.race([
    fetch(request),
    new Promise((_, reject) => 
      setTimeout(() => reject(new Error('Network timeout')), timeout)
    )
  ]);
}

// Helper function to determine cache strategy based on request
function getCacheStrategy(request) {
  const url = new URL(request.url);
  
  // Skip external resources
  if (!url.origin.includes(self.location.origin)) {
    return 'network-only';
  }
  
  // Static assets - cache first, then network
  if (
    request.url.includes('/static/') || 
    request.url.includes('/icons/') || 
    request.url.includes('/manifest.json')
  ) {
    return 'cache-first';
  }
  
  // API requests - network first, fallback to cache
  if (
    request.url.includes('/api/') || 
    request.url.includes('/app/lists/') ||
    (request.method === 'GET' && request.headers.get('accept')?.includes('application/json'))
  ) {
    return 'network-first';
  }
  
  // Images - cache first with network fallback
  if (
    request.url.match(/\.(?:png|jpg|jpeg|svg|gif|webp)$/) ||
    request.url.includes('/img/') ||
    request.url.includes('/images/')
  ) {
    return 'stale-while-revalidate';
  }
  
  // HTML pages - network first with cache fallback
  if (request.mode === 'navigate' || request.headers.get('accept')?.includes('text/html')) {
    return 'network-first';
  }
  
  // Default - network first
  return 'network-first';
}

// Fetch event - handle different caching strategies
self.addEventListener('fetch', event => {
  // Skip non-GET requests and browser extension requests
  if (event.request.method !== 'GET' || event.request.url.startsWith('chrome-extension://')) {
    return;
  }

  // Skip localhost/127.0.0.1 requests in development to avoid HTTPS issues
  const url = new URL(event.request.url);
  if (url.hostname === 'localhost' || url.hostname === '127.0.0.1' || url.hostname.includes('0.0.0.0')) {
    return;
  }

  const strategy = getCacheStrategy(event.request);
  
  // Apply appropriate caching strategy
  switch (strategy) {
    case 'cache-first':
      event.respondWith(cacheFirst(event.request));
      break;
      
    case 'network-first':
      event.respondWith(networkFirst(event.request));
      break;
      
    case 'stale-while-revalidate':
      event.respondWith(staleWhileRevalidate(event.request));
      break;
      
    case 'network-only':
      event.respondWith(fetch(event.request));
      break;
      
    default:
      event.respondWith(networkFirst(event.request));
  }
});

// Cache first strategy
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetchWithTimeout(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('Service Worker: Cache first error', error);
    return getFallbackResponse(request);
  }
}

// Network first strategy
async function networkFirst(request) {
  try {
    const networkResponse = await fetchWithTimeout(request);
    if (networkResponse.ok) {
      const cacheName = request.url.includes('/api/') ? API_CACHE : DYNAMIC_CACHE;
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
      
      // Trim cache in background
      trimCache(cacheName, cacheName === API_CACHE ? API_CACHE_LIMIT : DYNAMIC_CACHE_LIMIT);
    }
    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network first failed, trying cache', error);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    return getFallbackResponse(request);
  }
}

// Stale while revalidate strategy
async function staleWhileRevalidate(request) {
  const cachedResponse = await caches.match(request);
  
  const fetchPromise = fetchWithTimeout(request)
    .then(async (networkResponse) => {
      if (networkResponse.ok) {
        const cache = await caches.open(IMAGE_CACHE);
        cache.put(request, networkResponse.clone());
        trimCache(IMAGE_CACHE, IMAGE_CACHE_LIMIT);
      }
      return networkResponse;
    })
    .catch(error => {
      console.error('Service Worker: Revalidation failed', error);
      return null;
    });
  
  return cachedResponse || fetchPromise || getFallbackResponse(request);
}

// Get fallback response based on request type
function getFallbackResponse(request) {
  if (request.headers.get('accept')?.includes('text/html')) {
    return caches.match('/app/offline/');
  }
  
  if (request.headers.get('accept')?.includes('image')) {
    // Return a placeholder image if available
    return new Response(
      '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="#ddd"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#999">Offline</text></svg>',
      { headers: { 'Content-Type': 'image/svg+xml' } }
    );
  }
  
  if (request.headers.get('accept')?.includes('application/json')) {
    return new Response(
      JSON.stringify({ error: 'Offline', message: 'No cached data available' }),
      { 
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
  
  return new Response('Offline', { 
    status: 503,
    headers: { 'Content-Type': 'text/plain' }
  });
}

// Background sync for offline operations
self.addEventListener('sync', event => {
  console.log('Service Worker: Background sync event fired', event.tag);
  
  if (event.tag === 'sync-shopping-lists') {
    event.waitUntil(syncShoppingLists());
  } else if (event.tag === 'sync-list-items') {
    event.waitUntil(syncListItems());
  } else if (event.tag.startsWith('sync-')) {
    // Generic sync handler
    event.waitUntil(syncOfflineData(event.tag));
  }
});

// Enhanced sync function with retry logic
async function syncOfflineData(tag) {
  const maxRetries = 3;
  let retryCount = 0;
  
  while (retryCount < maxRetries) {
    try {
      const db = await openDatabase();
      const pendingSyncs = await getPendingSyncs(db, tag);
      
      for (const syncItem of pendingSyncs) {
        try {
          const response = await fetch(syncItem.url, {
            method: syncItem.method,
            headers: syncItem.headers,
            body: JSON.stringify(syncItem.data)
          });
          
          if (response.ok) {
            await removeSyncItem(db, syncItem.id);
          } else if (response.status >= 400 && response.status < 500) {
            // Client error - remove from sync as it won't succeed
            console.error('Client error, removing from sync:', response.status);
            await removeSyncItem(db, syncItem.id);
          }
        } catch (error) {
          console.error('Error syncing item:', error);
          // Network error - will retry
        }
      }
      
      console.log('Service Worker: Sync completed successfully');
      return true;
    } catch (error) {
      console.error('Service Worker: Sync error, retrying...', error);
      retryCount++;
      await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
    }
  }
  
  console.error('Service Worker: Sync failed after retries');
  return false;
}

// Database helper functions
async function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('shopsmart-offline', 2);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('syncQueue')) {
        db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

async function getPendingSyncs(db, tag) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['syncQueue'], 'readonly');
    const store = transaction.objectStore('syncQueue');
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const items = request.result.filter(item => item.tag === tag);
      resolve(items);
    };
  });
}

async function removeSyncItem(db, id) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['syncQueue'], 'readwrite');
    const store = transaction.objectStore('syncQueue');
    const request = store.delete(id);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

// Function to sync shopping lists
async function syncShoppingLists() {
  return syncOfflineData('sync-shopping-lists');
}

// Function to sync list items
async function syncListItems() {
  return syncOfflineData('sync-list-items');
}

// Push notification event
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  
  const options = {
    body: data.body || 'New update from ShopSmart',
    icon: '/static/icons/icon-144x144.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url || '/app/'
    },
    requireInteraction: true,
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/static/icons/icon-72x72.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'ShopSmart', options)
  );
});

// Notification click event
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'dismiss') {
    return;
  }
  
  const urlToOpen = event.notification.data.url || '/app/';
  
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    })
    .then(windowClients => {
      // Check if there's already a window open
      for (const client of windowClients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(urlToOpen);
          return client.focus();
        }
      }
      
      // Open new window
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Message handler for communication with clients
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => caches.delete(cacheName))
        );
      })
    );
  }
});

// Periodic background sync (if supported)
self.addEventListener('periodicsync', event => {
  if (event.tag === 'update-lists') {
    event.waitUntil(updateCachedLists());
  }
});

async function updateCachedLists() {
  try {
    const cache = await caches.open(API_CACHE);
    const requests = await cache.keys();
    
    // Update cached list data
    const listRequests = requests.filter(req => req.url.includes('/app/lists/'));
    
    for (const request of listRequests) {
      try {
        const response = await fetch(request);
        if (response.ok) {
          await cache.put(request, response);
        }
      } catch (error) {
        console.error('Failed to update cached list:', error);
      }
    }
  } catch (error) {
    console.error('Periodic sync error:', error);
  }
}

console.log('Service Worker: Enhanced service worker loaded');