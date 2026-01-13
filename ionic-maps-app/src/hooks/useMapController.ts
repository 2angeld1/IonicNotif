import { useEffect, useRef } from 'react';
import { useMap } from '@vis.gl/react-google-maps';
import type { LatLng, RouteInfo } from '../types';

export const useMapController = (
  start: LatLng | null,
  end: LatLng | null,
  route: RouteInfo | null,
  userLocation: LatLng | null | undefined,
  isRouteMode: boolean | undefined,
  userHeading: number | null | undefined
) => {
  const map = useMap();
  const lastRouteMode = useRef(isRouteMode);

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
      map.panTo(userLocation);
      
      // Solo forzar zoom al entrar al modo ruta
      if (!lastRouteMode.current) {
        map.setZoom(18);
        map.setTilt(45);
      }

      if (userHeading !== null && userHeading !== undefined) {
        map.setHeading(userHeading);
      }
    } 
    
    // Al salir del modo ruta, resetear la cámara una sola vez
    if (!isRouteMode && lastRouteMode.current) {
      map.setTilt(0);
      map.setHeading(0);
    }

    lastRouteMode.current = isRouteMode;
  }, [isRouteMode, userLocation, userHeading, map]);

  return map;
};
