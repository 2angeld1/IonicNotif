import { useState, useEffect } from 'react';
import type { LatLng } from '../types';

export const useUserLocation = (isRouteMode: boolean) => {
  const [userLocation, setUserLocation] = useState<LatLng | null>(null);
  const [userHeading, setUserHeading] = useState<number | null>(null);

  useEffect(() => {
    if (!navigator.geolocation) return;

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const coords = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        setUserLocation(coords);

        if (position.coords.heading !== null && !isNaN(position.coords.heading)) {
          setUserHeading(position.coords.heading);
        }
      },
      (error) => console.error('Error de ubicación:', error),
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 2000,
      }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  useEffect(() => {
    let lastUpdate = 0;
    const handleOrientation = (event: DeviceOrientationEvent) => {
      const now = Date.now();
      if (now - lastUpdate < 100) return; // Throttle: Máximo 10 actualizaciones por segundo

      if (event.alpha !== null && isRouteMode) {
        lastUpdate = now;
        const heading = (event as any).webkitCompassHeading ?? (360 - event.alpha);
        setUserHeading(heading);
      }
    };

    if (isRouteMode) {
      window.addEventListener('deviceorientation', handleOrientation, true);
    }

    return () => window.removeEventListener('deviceorientation', handleOrientation, true);
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
