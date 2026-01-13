import { useState, useEffect, useCallback } from 'react';
import { getRoute } from '../services/geocodingService';
import { sendNotification } from '../services/notificationService';
import { calculateDistance } from '../utils/geoUtils';
import type { LatLng, RouteInfo } from '../types';
import type { Incident } from '../services/apiService';

export const useNavigation = (
  userLocation: LatLng | null,
  incidents: Incident[]
) => {
  const [startLocation, setStartLocation] = useState<{ coords: LatLng | null; name: string }>({ coords: null, name: '' });
  const [endLocation, setEndLocation] = useState<{ coords: LatLng | null; name: string }>({ coords: null, name: '' });
  const [route, setRoute] = useState<RouteInfo | null>(null);
  const [isRouteMode, setIsRouteMode] = useState(false);
  const [isOffRoute, setIsOffRoute] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleCalculateRoute = useCallback(async (start?: LatLng, end?: LatLng) => {
    const s = start || startLocation.coords;
    const e = end || endLocation.coords;
    if (!s || !e) return null;

    setIsLoading(true);
    try {
      const result = await getRoute(s, e);
      if (result) setRoute(result);
      return result;
    } finally {
      setIsLoading(false);
    }
  }, [startLocation.coords, endLocation.coords]);

  const handleRecalculateRoute = useCallback(async () => {
    if (userLocation && endLocation.coords) {
      setStartLocation({ coords: userLocation, name: 'Mi ubicación' });
      setIsOffRoute(false);
      return await handleCalculateRoute(userLocation, endLocation.coords);
    }
    return null;
  }, [userLocation, endLocation.coords, handleCalculateRoute]);

  // Detección de fuera de ruta y notificaciones
  useEffect(() => {
    if (!isRouteMode || !userLocation || !route || route.coordinates.length === 0) {
      setIsOffRoute(false);
      return;
    }

    let minDistance = Infinity;
    for (const [lng, lat] of route.coordinates) {
      const dist = calculateDistance(userLocation.lat, userLocation.lng, lat, lng);
      if (dist < minDistance) minDistance = dist;
    }

    const isOff = minDistance > 50;
    if (isOff && !isOffRoute) {
      sendNotification('⚠️ Te has desviado de la ruta', {
        body: 'Pulsa aquí para recalcular la ruta automáticamente.',
        tag: 'off-route',
        renotify: true,
        requireInteraction: true,
        actions: [{ action: 'recalculate', title: 'Recalcular Ruta' }]
      });
    }
    setIsOffRoute(isOff);
  }, [userLocation, route, isRouteMode, isOffRoute]);

  // Notificaciones de incidencias y progreso
  useEffect(() => {
    if (!isRouteMode || !userLocation) return;

    // Incidencias
    const nearby = incidents.find(inc => 
      calculateDistance(userLocation.lat, userLocation.lng, inc.location.lat, inc.location.lng) < 500
    );
    if (nearby) {
      const key = `notified_incident_${nearby.id}`;
      if (!sessionStorage.getItem(key)) {
        sendNotification(`⚠️ Precaución: ${nearby.type}`, {
          body: `Incidencia a menos de 500m en tu ruta.`,
          tag: 'incident-alert'
        });
        sessionStorage.setItem(key, 'true');
      }
    }

    // Progreso
    if (endLocation.coords) {
      const distToEnd = calculateDistance(userLocation.lat, userLocation.lng, endLocation.coords.lat, endLocation.coords.lng);
      if (distToEnd < 1000 && distToEnd > 500) {
        if (!sessionStorage.getItem('notified_1km')) {
          sendNotification('📍 Cerca del destino', { body: 'A menos de 1 km.', tag: 'trip-status' });
          sessionStorage.setItem('notified_1km', 'true');
        }
      }
    }
  }, [userLocation, incidents, isRouteMode, endLocation.coords]);

  // Manejar mensajes del Service Worker
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'RECALCULATE_ROUTE') handleRecalculateRoute();
    };
    if ('serviceWorker' in navigator) navigator.serviceWorker.addEventListener('message', handleMessage);
    return () => { if ('serviceWorker' in navigator) navigator.serviceWorker.removeEventListener('message', handleMessage); };
  }, [handleRecalculateRoute]);

  // Limpiar estados de notificación al salir del modo ruta
  useEffect(() => {
    if (!isRouteMode) {
      sessionStorage.removeItem('notified_1km');
      // Podríamos limpiar incidencias específicas o todas las que empiecen por notified_
      Object.keys(sessionStorage)
        .filter(key => key.startsWith('notified_incident_'))
        .forEach(key => sessionStorage.removeItem(key));
    }
  }, [isRouteMode]);

  return {
    startLocation, setStartLocation,
    endLocation, setEndLocation,
    route, setRoute,
    isRouteMode, setIsRouteMode,
    isOffRoute, setIsOffRoute,
    isLoading,
    handleCalculateRoute,
    handleRecalculateRoute
  };
};
