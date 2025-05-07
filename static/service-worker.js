/**
 * Service Worker for ShopSmart
 * Provides offline functionality and caching
 */

// Cache names
const STATIC_CACHE = 'shopsmart-static-v2';
const DYNAMIC_CACHE = 'shopsmart-dynamic-v2';
const API_CACHE = 'shopsmart-api-v2';
const IMAGE_CACHE = 'shopsmart-images-v2';

// Resources to cache immediately on install
const STATIC_ASSETS = [
  '/', 
  '/app/',
  '/static/css/base.css',
  '/static/css/mobile.css',
  '/static/js/app.js',
  '/static/js/modal-handler.js',
  '/static/js/theme-manager.js',
  '/static/js/mobile-nav.js',
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
    await cache.delete(keys[0]);
    // Recursively trim until we're under the limit
    await trimCache(cacheName, maxItems);
  }
}

// Helper function to determine cache strategy based on request
function getCacheStrategy(request) {
  const url = new URL(request.url);
  
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
    (request.method === 'GET' && request.headers.get('accept')?.includes('application/json'))
  ) {
    return 'network-first';
  }
  
  // Images - cache first with network fallback
  if (
    request.url.match(/\.(?:png|jpg|jpeg|svg|gif)$/) ||
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

  const strategy = getCacheStrategy(event.request);
  
  // Apply appropriate caching strategy
  switch (strategy) {
    case 'cache-first':
      event.respondWith(
        caches.match(event.request)
          .then(cachedResponse => {
            if (cachedResponse) {
              return cachedResponse;
            }
            
            return fetch(event.request)
              .then(fetchResponse => {
                return caches.open(STATIC_CACHE)
                  .then(cache => {
                    cache.put(event.request, fetchResponse.clone());
                    return fetchResponse;
                  });
              })
              .catch(error => {
                console.error('Service Worker fetch error:', error);
                // Return offline fallback for HTML requests
                if (event.request.headers.get('accept')?.includes('text/html')) {
                  return caches.match('/app/offline/');
                }
                return new Response('Network error occurred', { status: 408, headers: { 'Content-Type': 'text/plain' } });
              });
          })
      );
      break;
      
    case 'network-first':
      event.respondWith(
        fetch(event.request)
          .then(fetchResponse => {
            const cacheName = event.request.url.includes('/api/') ? API_CACHE : DYNAMIC_CACHE;
            
            caches.open(cacheName)
              .then(cache => {
                cache.put(event.request, fetchResponse.clone());
                return trimCache(cacheName, DYNAMIC_CACHE_LIMIT);
              });
            
            return fetchResponse;
          })
          .catch(error => {
            console.log('Service Worker: Network request failed, falling back to cache', error);
            
            return caches.match(event.request)
              .then(cachedResponse => {
                if (cachedResponse) {
                  return cachedResponse;
                }
                
                // Return offline fallback for HTML requests
                if (event.request.headers.get('accept')?.includes('text/html')) {
                  return caches.match('/app/offline/');
                }
                
                return new Response('Network error occurred', { status: 408, headers: { 'Content-Type': 'text/plain' } });
              });
          })
      );
      break;
      
    case 'stale-while-revalidate':
      event.respondWith(
        caches.match(event.request)
          .then(cachedResponse => {
            const fetchPromise = fetch(event.request)
              .then(fetchResponse => {
                caches.open(IMAGE_CACHE)
                  .then(cache => {
                    cache.put(event.request, fetchResponse.clone());
                    return trimCache(IMAGE_CACHE, DYNAMIC_CACHE_LIMIT);
                  });
                
                return fetchResponse;
              })
              .catch(error => {
                console.error('Service Worker image fetch error:', error);
              });
            
            return cachedResponse || fetchPromise;
          })
      );
      break;
      
    default:
      // Default to network with cache fallback
      event.respondWith(
        fetch(event.request)
          .then(fetchResponse => {
            return fetchResponse;
          })
          .catch(error => {
            console.log('Service Worker: Network request failed, falling back to cache', error);
            return caches.match(event.request);
          })
      );
  }
});

// Background sync for offline operations
self.addEventListener('sync', event => {
  console.log('Service Worker: Background sync event fired', event.tag);
  
  if (event.tag === 'sync-shopping-lists') {
    event.waitUntil(syncShoppingLists());
  } else if (event.tag === 'sync-list-items') {
    event.waitUntil(syncListItems());
  }
});

// Function to sync shopping lists
async function syncShoppingLists() {
  try {
    // Open IndexedDB
    const db = await new Promise((resolve, reject) => {
      const request = indexedDB.open('groceryBuddyDB', 1);
      request.onerror = reject;
      request.onsuccess = () => resolve(request.result);
    });
    
    // Get all pending sync items
    const transaction = db.transaction(['syncLog'], 'readonly');
    const store = transaction.objectStore('syncLog');
    const pendingSyncs = await new Promise((resolve, reject) => {
      const request = store.getAll();
      request.onerror = reject;
      request.onsuccess = () => resolve(request.result);
    });
    
    // Process each pending sync
    for (const syncItem of pendingSyncs) {
      if (syncItem.model_name === 'shopping_list') {
        // Send data to server
        const response = await fetch('/api/lists/sync/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': syncItem.data.csrf_token
          },
          body: JSON.stringify(syncItem.data)
        });
        
        if (response.ok) {
          // Remove from sync log if successful
          const deleteTransaction = db.transaction(['syncLog'], 'readwrite');
          const deleteStore = deleteTransaction.objectStore('syncLog');
          await new Promise((resolve, reject) => {
            const request = deleteStore.delete(syncItem.timestamp);
            request.onerror = reject;
            request.onsuccess = resolve;
          });
        }
      }
    }
    
    console.log('Service Worker: Shopping lists synced successfully');
    return true;
  } catch (error) {
    console.error('Service Worker: Error syncing shopping lists', error);
    return false;
  }
}

// Function to sync list items
async function syncListItems() {
  // Similar implementation to syncShoppingLists
  // but for list items
  console.log('Service Worker: List items sync not yet implemented');
  return true;
}

// Push notification event
self.addEventListener('push', event => {
  const data = event.data.json();
  
  const options = {
    body: data.body,
    icon: '/static/icons/icon-144x144.png',
    vibrate: [100, 50, 100],
    data: {
      url: data.url
    },
    actions: [
      {
        action: 'view',
        title: 'View'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'view') {
    const urlToOpen = event.notification.data.url || '/';
    
    event.waitUntil(
      clients.matchAll({
        type: 'window',
        includeUncontrolled: true
      })
      .then(windowClients => {
        // Check if there's already a window open
        for (const client of windowClients) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
    );
  }
});