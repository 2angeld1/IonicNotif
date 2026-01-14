import { useState, useEffect, useRef, useCallback } from 'react';
import type { LatLng, RouteInfo } from '../types';
import { calculateRouteHeading, interpolatePosition, interpolateHeading } from '../utils/geoUtils';

export const useUserLocation = (isRouteMode: boolean, route?: RouteInfo | null) => {
  const [userLocation, setUserLocation] = useState<LatLng | null>(null);
  const [userHeading, setUserHeading] = useState<number | null>(null);

  // Referencias para suavizado
  const smoothedPositionRef = useRef<LatLng | null>(null);
  const smoothedHeadingRef = useRef<number>(0);
  const animationFrameRef = useRef<number | null>(null);
  const lastGpsPositionRef = useRef<LatLng | null>(null);

  // Función para actualizar posición suavemente usando requestAnimationFrame
  const smoothUpdate = useCallback(() => {
    if (!lastGpsPositionRef.current) {
      animationFrameRef.current = requestAnimationFrame(smoothUpdate);
      return;
    }

    const targetPosition = lastGpsPositionRef.current;

    // Inicializar posición suavizada si no existe
    if (!smoothedPositionRef.current) {
      smoothedPositionRef.current = targetPosition;
    }

    // Interpolar posición
    smoothedPositionRef.current = interpolatePosition(
      smoothedPositionRef.current,
      targetPosition,
      0.12 // Factor de suavizado para movimiento fluido
    );

    // Calcular heading basado en la ruta si estamos en modo navegación
    if (isRouteMode && route?.coordinates && targetPosition) {
      const routeHeading = calculateRouteHeading(
        targetPosition.lat,
        targetPosition.lng,
        route.coordinates
      );

      if (routeHeading !== null) {
        smoothedHeadingRef.current = interpolateHeading(
          smoothedHeadingRef.current,
          routeHeading,
          0.08 // Factor más suave para rotación
        );
        setUserHeading(smoothedHeadingRef.current);
      }
    }

    // Solo actualizar el estado si hay cambio significativo (performance)
    const currentSmoothed = smoothedPositionRef.current;
    const prevLocation = userLocation;

    if (!prevLocation ||
      Math.abs(currentSmoothed.lat - prevLocation.lat) > 0.000001 ||
      Math.abs(currentSmoothed.lng - prevLocation.lng) > 0.000001) {
      setUserLocation({ ...currentSmoothed });
    }

    animationFrameRef.current = requestAnimationFrame(smoothUpdate);
  }, [isRouteMode, route, userLocation]);

  // Iniciar/detener loop de animación
  useEffect(() => {
    if (isRouteMode) {
      animationFrameRef.current = requestAnimationFrame(smoothUpdate);
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isRouteMode, smoothUpdate]);

  // Seguimiento GPS
  useEffect(() => {
    if (!navigator.geolocation) return;

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const coords = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };

        // Guardar posición GPS para el suavizado
        lastGpsPositionRef.current = coords;

        // Si NO estamos en modo ruta, actualizar directamente
        if (!isRouteMode) {
          setUserLocation(coords);

          // Usar heading del GPS si está disponible
          if (position.coords.heading !== null && !isNaN(position.coords.heading)) {
            setUserHeading(position.coords.heading);
          }
        }
      },
      (error) => console.error('Error de ubicación:', error),
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 1000, // Reducido para actualizaciones más frecuentes
      }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, [isRouteMode]);

  // Limpiar heading cuando cambia el modo
  useEffect(() => {
    if (!isRouteMode) {
      smoothedHeadingRef.current = 0;
    }
  }, [isRouteMode]);

  const handleRecenter = () => {
    if (userLocation) {
      const coords = { ...userLocation };
      setUserLocation(null);
      setTimeout(() => setUserLocation(coords), 10);
    }
  };

  return { userLocation, userHeading, handleRecenter };
};
