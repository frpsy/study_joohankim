/* Fast, offline-tolerant navigation for public static study pages only.
   No personal account or learning record resources are cached. */
const VERSION = new URL(self.location.href).searchParams.get('v') || 'unversioned';
const CACHE = 'study-home-static-' + VERSION;
const PREFIX = 'study-home-static-';
const CORE = [
  './', './index.html', './offline.html',
  './manifest.webmanifest', './assets/icon-512.png', './assets/apple-touch-icon.png',
  './assets/site.css', './assets/site.js', './assets/theme.js'
];
const root = new URL(self.registration.scope);

function isStaticSiteResource(request) {
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== root.origin || !url.pathname.startsWith(root.pathname)) return false;
  if (request.mode === 'navigate') return true;
  return ['style', 'script', 'image', 'font', 'manifest'].includes(request.destination);
}
async function update(cache, request, isNavigation = false) {
  try {
    const response = await fetch(request);
    if (response.ok && response.type === 'basic') {
      // Ignore refresh/version query parameters in the stored HTML key, so the
      // next offline visit never resurrects an older page from an old cache entry.
      const key = isNavigation || request.mode === 'navigate'
        ? new Request(new URL(request.url).origin + new URL(request.url).pathname)
        : request;
      await cache.put(key, response.clone());
    }
    return response;
  } catch { return null; }
}

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    // Save the small public reading library for genuinely offline installed use.
    let pages=[];
    try{
      const response=await fetch(new URL('./lectures.json',root),{cache:'no-store'});
      if(response.ok){
        await cache.put(new URL('./lectures.json',root),response.clone());
        const rows=await response.json();
        pages=rows.filter(row=>typeof row.id==='string' && /^[a-zA-Z0-9_-]+$/.test(row.id))
          .map(row=>'./lectures/'+row.id+'.html');
      }
    }catch{}
    await Promise.allSettled([...CORE,...pages].map(path=>update(cache,new Request(new URL(path,root),{cache:'reload'}))));
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
    // Navigation must be network-first. Cache-first HTML can indefinitely show
    // an old header even when build-info.json reports a newer deployment.
    if (request.mode === 'navigate') {
      const fresh = await update(cache, new Request(request, {cache:'no-store'}), true);
      if (fresh) return fresh;
      return await cache.match(request, {ignoreSearch:true})
        || await cache.match(new URL('./offline.html',root))
        || Response.error();
    }
    // Static CSS/JS and images stay cache-first for fast repeat reading.
    if (request.cache === 'reload' || new URL(request.url).searchParams.has('refresh')) {
      const fresh = await update(cache, request);
      if (fresh) return fresh;
    }
    // A versioned URL (?v=…) is a new build: use only that exact copy, never an older
    // build's file that merely shares the path, so new HTML never runs old CSS/JS.
    if (new URL(request.url).searchParams.has('v')) {
      const exact = await cache.match(request);
      if (exact) return exact;
      const fresh = await update(cache, new Request(request, {cache:'reload'}));
      if (fresh) return fresh;
    }
    const cached = await cache.match(request, {ignoreSearch:true});
    if (cached) {
      event.waitUntil(update(cache, request));
      return cached;
    }
    return await update(cache, request) || Response.error();
  })());
});
