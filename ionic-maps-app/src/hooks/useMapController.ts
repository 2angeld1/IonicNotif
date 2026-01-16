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
      // Throttle de panTo para evitar actualizaciones excesivas
      const now = Date.now();
      if (now - lastPanTimeRef.current > 50) { // Máximo 20 FPS para la cámara
        map.panTo(userLocation);
        lastPanTimeRef.current = now;
      }
      
      // Forzar configuración inicial al entrar al modo ruta O cuando cambia la ruta (recálculo)
      const routeChanged = route !== lastRouteRef.current && route !== null;
      if (!lastRouteMode.current || routeChanged) {
        // Zoom más cercano y mayor inclinación para mejor experiencia de navegación
        map.setZoom(19);
        map.setTilt(60); // Mayor inclinación para vista más inmersiva
      }

      // Actualizar heading de la cámara (la cámara mira en la dirección del heading)
      // Esto hace que siempre estemos mirando "hacia adelante" en la ruta
      if (userHeading !== null && userHeading !== undefined) {
        map.setHeading(userHeading);
      }
    } 
    
    // Al salir del modo ruta, resetear la cámara una sola vez
    if (!isRouteMode && lastRouteMode.current) {
      map.setTilt(0);
      map.setHeading(0);
      map.setZoom(15);
    }

    lastRouteMode.current = isRouteMode;
    lastRouteRef.current = route;
  }, [isRouteMode, userLocation, userHeading, map, route]);

  return map;
};

