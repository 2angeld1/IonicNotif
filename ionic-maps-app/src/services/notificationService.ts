/**
 * Servicio para gestionar notificaciones nativas del navegador
 * Soporta acciones (botones) si hay Service Worker disponible
 */

export const requestNotificationPermission = async (): Promise<boolean> => {
  if (!('Notification' in window)) {
    console.warn('Este navegador no soporta notificaciones de escritorio');
    return false;
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  const permission = await Notification.requestPermission();
  return permission === 'granted';
};

interface NotificationAction {
  action: string;
  title: string;
  icon?: string;
}

interface NotificationOptions {
  body?: string;
  icon?: string;
  tag?: string;
  renotify?: boolean;
  silent?: boolean;
  actions?: NotificationAction[];
  requireInteraction?: boolean;
}

export const sendNotification = async (title: string, options: NotificationOptions = {}) => {
  if (Notification.permission !== 'granted') {
    return;
  }

  const defaultIcon = '/icon.png';
  const finalOptions = {
    icon: defaultIcon,
    badge: defaultIcon,
    ...options
  };

  try {
    // Intentar usar Service Worker para soportar acciones (botones)
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.ready;
      if (registration) {
        await registration.showNotification(title, finalOptions);
        return;
      }
    }
  } catch (error) {
    console.log('SW Notification failed, falling back to standard', error);
  }

  // Fallback a notificación normal (sin botones de acción) si no hay SW o falla
  // Las notificaciones normales no soportan 'actions'
  const { actions, ...standardOptions } = finalOptions;
  new Notification(title, standardOptions as any);
};

export const clearNotifications = async (tag?: string) => {
  if ('serviceWorker' in navigator) {
    const registration = await navigator.serviceWorker.ready;
    const notifications = await registration.getNotifications(tag ? { tag } : undefined);
    notifications.forEach(n => n.close());
  }
};
