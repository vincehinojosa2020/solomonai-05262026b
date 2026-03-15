// Solomon AI Service Worker v4 — minimal, no static caching
const CACHE_NAME = 'solomon-ai-v4';

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

// Only handle push notifications — NO fetch caching
self.addEventListener('push', (event) => {
  let data = { title: 'Solomon AI', body: 'You have a new notification', url: '/portal' };
  try { data = event.data.json(); } catch (e) {}
  event.waitUntil(self.registration.showNotification(data.title, {
    body: data.body,
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-72.png',
    vibrate: [100, 50, 100],
    data: { url: data.url || '/portal' },
    actions: [
      { action: 'open', title: 'Open' },
      { action: 'dismiss', title: 'Dismiss' }
    ]
  }));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'dismiss') return;
  const url = event.notification.data?.url || '/portal';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((wc) => {
      for (const c of wc) { if (c.url.includes(url) && 'focus' in c) return c.focus(); }
      return clients.openWindow(url);
    })
  );
});
