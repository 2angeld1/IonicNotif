import { useEffect, useRef } from 'react';
import { useMap } from '@vis.gl/react-google-maps';
import type { LatLng, RouteInfo } from '../types';

export const useMapController = (
  start: LatLng | null,
  end: LatLng | null,
  route: RouteInfo | null,
  userLocation: LatLng | null | undefined,
  isRouteMode: boolean | undefined,
  userHeading: number | null | undefined,
  recenterTrigger: number | undefined
) => {
  const map = useMap();
  const lastRouteMode = useRef(isRouteMode);
  const lastPanTimeRef = useRef(0);
  const lastRouteRef = useRef<RouteInfo | null>(null);

  // 1. Ajustar límites solo cuando cambia la ruta o los destinos (no con el GPS)
  useEffect(() => {
    if (!map) return;

    if (route && route.coordinates.length > 1) {
      const bounds = new google.maps.LatLngBounds();
      route.coordinates.forEach(([lng, lat]) => bounds.extend({ lat, lng }));
      map.fitBounds(bounds, { top: 60, right: 60, bottom: 60, left: 60 });
    } else if (start && end) {
      const bounds = new google.maps.LatLngBounds();
      bounds.extend(start);
      bounds.extend(end);
      map.fitBounds(bounds, { top: 60, right: 60, bottom: 60, left: 60 });
    }
  }, [route, start, end, map]);

  // 2. Control inteligente de Navegación
  useEffect(() => {
    if (!map) return;

    // Solo mover la cámara si estamos en modo ruta
    if (isRouteMode && userLocation) {
      const now = Date.now();

      // Control de Jitter y Throttle (limitado a 60-100ms para evitar sobrecarga de red)
      if (now - lastPanTimeRef.current > 60) {
        const updateOptions: google.maps.CameraOptions = {
          center: userLocation,
          tilt: 60, // Mantener tilt inmersivo
          zoom: 19  // Mantener zoom cercano
        };

        // Solo actualizar heading si el cambio es significativo (> 3 grados) para evitar jitter y re-fetching de tiles
        const currentHeading = map.getHeading() || 0;
        let newHeading = currentHeading;

        if (userHeading !== null && userHeading !== undefined) {
          const diff = Math.abs((userHeading - currentHeading + 180) % 360 - 180);
          if (diff > 3) { // Umbral de 3 grados
            newHeading = userHeading;
          }
        }
        updateOptions.heading = newHeading;

        map.moveCamera(updateOptions);
        lastPanTimeRef.current = now;
      }
      
      // Forzar configuración inicial al entrar al modo ruta
      if (!lastRouteMode.current) {
        // Ajuste inicial agresivo (sin threshold)
        map.moveCamera({
          center: userLocation,
          zoom: 19,
          tilt: 60,
          heading: userHeading || 0
        });
      }

    } 
    
    // Al salir del modo ruta, resetear la cámara una sola vez
    if (!isRouteMode && lastRouteMode.current) {
      map.moveCamera({
        tilt: 0,
        heading: 0,
        zoom: 15
      });
    }

    lastRouteMode.current = isRouteMode;
    lastRouteRef.current = route;
  }, [isRouteMode, userLocation, userHeading, map, route]);

  // 3. Centrar manualmente al disparar el trigger
  useEffect(() => {
    if (map && userLocation && recenterTrigger && recenterTrigger > 0) {
      map.panTo(userLocation);
      // Opcionalmente ajustar el zoom
      if (!isRouteMode) map.setZoom(17);
    }
  }, [recenterTrigger, map, userLocation, isRouteMode]);

  return map;
};

