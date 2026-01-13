// Service Worker mejorado para PWA y Notificaciones
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// Manejar fetch: Ignorar peticiones de Google Maps para no saturar la caché/red
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Lista de dominios de Google Maps a ignorar
  if (url.hostname.includes('googleapis.com') ||
    url.hostname.includes('gstatic.com') ||
    url.hostname.includes('googleusercontent.com')) {
    return; // Dejar que el navegador maneje estas peticiones directamente
  }

  // Estrategia Network First para el resto
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});

// Manejar clics en notificaciones
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  // Si el usuario hizo clic en el botón de acción "recalculate"
  if (event.action === 'recalculate') {
    // Abrir o enfocar la ventana de la app y enviarle un mensaje
    event.waitUntil(
      self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
        // Intentar enfocar una ventana existente
        for (const client of clientList) {
          if (client.url && 'focus' in client) {
            client.focus();
            client.postMessage({ type: 'RECALCULATE_ROUTE' });
            return;
          }
        }
        // Si no hay ventana abierta, abrir una (opcional, aquí asumo que está en segundo plano)
        if (self.clients.openWindow) {
          return self.clients.openWindow('/').then(client => {
            if (client) {
              setTimeout(() => client.postMessage({ type: 'RECALCULATE_ROUTE' }), 1000);
            }
          });
        }
      })
    );
  } else {
    // Clic normal en el cuerpo de la notificación -> Solo enfocar
    event.waitUntil(
      self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
        for (const client of clientList) {
          if (client.url && 'focus' in client) {
            return client.focus();
          }
        }
        if (self.clients.openWindow) {
          return self.clients.openWindow('/');
        }
      })
    );
  }
});
