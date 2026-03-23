const CACHE_NAME = 'vrb-v3';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  var url = e.request.url;

  // HTML pages: always fetch fresh, never serve stale cache
  if (url.endsWith('.html') || url.endsWith('/')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  // Static assets (JS, CSS, images): network-first with cache fallback
  e.respondWith(
    fetch(e.request)
      .then((response) => {
        var clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(e.request, clone));
        return response;
      })
      .catch(() => caches.match(e.request))
  );
});

// Handle push notifications
self.addEventListener('push', (e) => {
  var data = { title: 'Viral Reply Bot', body: 'New suggestions ready' };
  try {
    data = e.data.json();
  } catch(err) {
    data.body = e.data ? e.data.text() : 'New suggestions ready';
  }

  e.waitUntil(
    self.registration.showNotification(data.title || 'Viral Reply Bot', {
      body: data.body || 'New suggestions ready to post',
      icon: 'icon-192.png',
      badge: 'icon-192.png',
      data: { url: data.url || '/viral-reply-dashboard/' },
    })
  );
});

// Open app when notification is tapped
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  var url = e.notification.data && e.notification.data.url
    ? e.notification.data.url
    : '/viral-reply-dashboard/';
  e.waitUntil(
    clients.matchAll({ type: 'window' }).then((list) => {
      for (var c of list) {
        if (c.url.includes('viral-reply-dashboard') && 'focus' in c) return c.focus();
      }
      return clients.openWindow(url);
    })
  );
});
