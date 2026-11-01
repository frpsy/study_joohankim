/* Fast, offline-tolerant navigation for public static study pages only.
   Firestore, authentication, cross-origin SDKs and mutable user data are NEVER cached. */
const VERSION = '20261101-native-timeline-v3';
const CACHE = 'study-home-static-' + VERSION;
const PREFIX = 'study-home-static-';
const CORE = [
  './', './index.html', './concepts.html', './study-history.html',
  './assets/site.css', './assets/site.js'
];
const root = new URL(self.registration.scope);

function isStaticSiteResource(request) {
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== root.origin || !url.pathname.startsWith(root.pathname)) return false;
  if (request.mode === 'navigate') return true;
  return ['style', 'script', 'image', 'font'].includes(request.destination);
}
async function update(cache, request) {
  try {
    const response = await fetch(request);
    if (response.ok && response.type === 'basic') {
      await cache.put(request, response.clone());
    }
    return response;
  } catch { return null; }
}

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await Promise.allSettled(CORE.map(path => update(cache, new Request(new URL(path, root)))));
  })());
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k.startsWith(PREFIX) && k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  const request = event.request;
  if (!isStaticSiteResource(request)) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    // Explicit reloads always check the network first to get recently published content.
    if (request.cache === 'reload' || new URL(request.url).searchParams.has('refresh')) {
      const fresh = await update(cache, request);
      if (fresh) return fresh;
    }
    const cached = await cache.match(request, {ignoreSearch: true});
    if (cached) {
      event.waitUntil(update(cache, request));
      return cached;
    }
    const fresh = await update(cache, request);
    return fresh || Response.error();
  })());
});
