// Service Worker básico para permitir la instalación de la PWA
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  // Solo passthrough, necesario para que Chrome detecte la PWA
  event.respondWith(fetch(event.request));
});
