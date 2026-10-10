// Gym-Bro offline cache. Bump VERSION on every update.
const VERSION = "gym-bro-v48";
const CORE = ["./", "index.html", "profile.js", "data.js", "guides.js", "manifest.webmanifest", "icon-192.png", "icon-512.png"];

self.addEventListener("install", (e) => {
  // "reload" skips the browser's HTTP cache so a new version installs fresh files.
  e.waitUntil(caches.open(VERSION)
    .then((c) => c.addAll(CORE.map((u) => new Request(u, { cache: "reload" }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// App files: always check the server first (so updates show on the next open), fall back to the cache offline.
function networkFirst(req, cacheKey) {
  const url = typeof req === "string" ? req : req.url;
  return fetch(url, { cache: "no-cache" })
    .then((r) => { if (r.ok) { const copy = r.clone(); caches.open(VERSION).then((c) => c.put(cacheKey || req, copy)); } return r; })
    .catch(() => caches.match(cacheKey || req, { ignoreSearch: true }));
}

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (e.request.mode === "navigate") { e.respondWith(networkFirst(e.request.url, "index.html")); return; }
  if (url.origin === location.origin) { e.respondWith(networkFirst(e.request)); return; }
  // Fonts: cache first, they never change.
  if (url.hostname.endsWith("gstatic.com") || url.hostname.endsWith("googleapis.com")) {
    e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request).then((r) => {
      if (r.ok || r.type === "opaque") { const copy = r.clone(); caches.open(VERSION).then((c) => c.put(e.request, copy)); }
      return r;
    })));
  }
});

// Tapping a timer notification brings the app to the front.
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((cs) => cs.length ? cs[0].focus() : self.clients.openWindow("./")));
});
