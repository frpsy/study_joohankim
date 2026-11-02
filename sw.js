/* Fast, offline-tolerant navigation for public static study pages only.
   No personal account or learning record resources are cached. */
const VERSION = new URL(self.location.href).searchParams.get('v') || 'unversioned';
const CACHE = 'study-home-static-' + VERSION;
const PREFIX = 'study-home-static-';
const CORE = [
  './', './index.html', './concepts.html', './offline.html',
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
    // Save the small public reading library for genuinely offline installed use.
    let pages=[];
    try{
      const response=await fetch(new URL('./lectures.json',root),{cache:'no-store'});
      if(response.ok){
        await cache.put(new URL('./lectures.json',root),response.clone());
        const rows=await response.json();
        pages=rows.filter(row=>typeof row.id==='string' && /^[a-zA-Z0-9_-]+$/.test(row.id))
          .flatMap(row=>['lectures','mini-courses','summaries'].map(folder=>'./'+folder+'/'+row.id+'.html'));
      }
    }catch{}
    await Promise.allSettled([...CORE,...pages].map(path=>update(cache,new Request(new URL(path,root)))));
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
    if(fresh)return fresh;
    if(request.mode==='navigate')return await cache.match(new URL('./offline.html',root)) || Response.error();
    return Response.error();
  })());
});
