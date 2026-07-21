// PMD Reception — Service Worker v6
var CACHE_NAME = 'pmd-reception-v8';
var STATIC_ASSETS = [
  '/static/css/app.css',
  '/static/js/app.js',
  '/static/js/scanner.js',
  '/static/js/queue.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

var HTML_PAGES = ['/', '/scan', '/log'];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      cache.addAll(STATIC_ASSETS);
      return cache.addAll(HTML_PAGES);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k !== CACHE_NAME; })
            .map(function(k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function(event) {
  var url = event.request.url;

  // Never cache API calls
  if (url.includes('/api/')) {
    event.respondWith(
      fetch(event.request).catch(function() {
        return new Response(
          JSON.stringify({ success: false, message: 'Hors ligne', active: false }),
          { headers: { 'Content-Type': 'application/json' } }
        );
      })
    );
    return;
  }

  // Never cache admin routes
  if (url.includes('/admin')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // HTML pages - network first, fall back to cached version
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(function(response) {
          var clone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(event.request, clone);
          });
          return response;
        })
        .catch(function() {
          return caches.match(event.request).then(function(cached) {
            if (cached) return cached;
            return caches.match('/');
          });
        })
    );
    return;
  }

  // Stale-while-revalidate for static assets
  event.respondWith(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.match(event.request).then(function(cached) {
        var fetchPromise = fetch(event.request).then(function(response) {
          if (response && response.status === 200) {
            cache.put(event.request, response.clone());
          }
          return response;
        }).catch(function() {
          return cached;
        });
        return cached || fetchPromise;
      });
    })
  );
});