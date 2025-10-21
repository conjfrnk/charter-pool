// Service Worker for Charter Pool PWA
const CACHE_NAME = 'charter-pool-v1';
const urlsToCache = [
  '/',
  '/static/style.css',
  '/static/modern-ui.css',
  '/static/main.js',
  '/static/modern-ui.js',
  '/static/pcc_logo.png',
  '/leaderboard',
  '/login'
];

// Install Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }

        // Clone the request
        const fetchRequest = event.request.clone();

        return fetch(fetchRequest).then(response => {
          // Check if valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });

          return response;
        });
      })
      .catch(() => {
        // Offline fallback
        if (event.request.destination === 'document') {
          return caches.match('/');
        }
      })
  );
});

// Activate Service Worker and clean old caches
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];

  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for offline game submissions
self.addEventListener('sync', event => {
  if (event.tag === 'submit-game') {
    event.waitUntil(submitPendingGames());
  }
});

async function submitPendingGames() {
  const db = await openDB();
  const tx = db.transaction('pending-games', 'readonly');
  const store = tx.objectStore('pending-games');
  const games = await store.getAll();

  for (const game of games) {
    try {
      const response = await fetch('/report-game', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(game)
      });

      if (response.ok) {
        // Remove from pending if successful
        const deleteTx = db.transaction('pending-games', 'readwrite');
        await deleteTx.objectStore('pending-games').delete(game.id);
      }
    } catch (error) {
      console.error('Failed to submit game:', error);
    }
  }
}

// Push notifications
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'New update from Charter Pool',
    icon: '/static/pcc_logo.png',
    badge: '/static/pcc_logo.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    }
  };

  event.waitUntil(
    self.registration.showNotification('Charter Pool', options)
  );
});

// Notification click
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/')
  );
});
