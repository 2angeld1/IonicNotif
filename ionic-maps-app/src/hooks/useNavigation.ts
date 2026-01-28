import { useState, useEffect, useCallback, useRef } from 'react';
import { getRoute, getRouteAlternatives } from '../services/geocodingService';
import { predictExternalRoutes } from '../services/apiService';
import { sendNotification } from '../services/notificationService';
import { calculateDistance, distanceToSegment } from '../utils/geoUtils';
import { useVoiceMode } from '../contexts/VoiceModeContext';
import type { LatLng, RouteInfo } from '../types';
import type { Incident } from '../services/apiService';

export const useNavigation = (
  userLocation: LatLng | null,
  incidents: Incident[]
) => {
  const [startLocation, setStartLocation] = useState<{ coords: LatLng | null; name: string }>({ coords: null, name: '' });
  const [endLocation, setEndLocation] = useState<{ coords: LatLng | null; name: string }>({ coords: null, name: '' });
  const [route, setRoute] = useState<RouteInfo | null>(null);
  const [alternativeRoutes, setAlternativeRoutes] = useState<RouteInfo[]>([]);
  const [selectedRouteIndex, setSelectedRouteIndex] = useState(0);
  const [mlRecommendedIndex, setMlRecommendedIndex] = useState<number | null>(null);
  const [isRouteMode, setIsRouteMode] = useState(false);
  const [isOffRoute, setIsOffRoute] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Usar el contexto de voz centralizado
  const { speak } = useVoiceMode();

  // Referencia para el debounce de fuera de ruta
  const offRouteCounterRef = useRef(0);

  // Calcular rutas con alternativas y predicciones ML
  const handleCalculateRoute = useCallback(async (start?: LatLng, end?: LatLng) => {
    const s = start || startLocation.coords;
    const e = end || endLocation.coords;
    if (!s || !e) return null;

    setIsLoading(true);
    try {
      // 1. Obtener rutas alternativas de Google Maps
      const alternatives = await getRouteAlternatives(s, e);

      if (alternatives.length > 0) {
        // 2. Enviar rutas al backend para predicciones ML
        const mlPredictions = await predictExternalRoutes(
          s,
          alternatives.map(r => ({
            distance: r.distance,
            duration: r.duration,
            coordinates: r.coordinates
          }))
        );

        // 3. Combinar datos de Google con predicciones ML
        const enrichedAlternatives: RouteInfo[] = alternatives.map((alt, idx) => {
          const prediction = mlPredictions?.predictions.find(p => p.index === idx);
          return {
            ...alt,
            predicted_duration: prediction?.predicted_duration || alt.duration,
            ml_confidence: prediction?.confidence || 0,
            ml_recommended: mlPredictions?.recommended_index === idx,
            incidents_count: prediction?.incidents_count || 0
          };
        });

        // 4. Ordenar por tiempo predicho por ML (si existe)
        enrichedAlternatives.sort((a, b) =>
          (a.predicted_duration || a.duration) - (b.predicted_duration || b.duration)
        );

        // Guardar índice recomendado por ML
        const recommendedIdx = mlPredictions?.recommended_index ?? 0;
        setMlRecommendedIndex(recommendedIdx);

        setAlternativeRoutes(enrichedAlternatives);
        setSelectedRouteIndex(0);
        setRoute(enrichedAlternatives[0]); // Seleccionar la mejor según ML
        setIsOffRoute(false);
        offRouteCounterRef.current = 0;

        return enrichedAlternatives[0];
      } else {
      // Fallback a ruta única si no hay alternativas
        const result = await getRoute(s, e);
        if (result) {
          setRoute(result);
          setAlternativeRoutes([result]);
          setSelectedRouteIndex(0);
          setMlRecommendedIndex(null);
          setIsOffRoute(false);
          offRouteCounterRef.current = 0;
        }
        return result;
      }
    } finally {
      setIsLoading(false);
    }
  }, [startLocation.coords, endLocation.coords]);

  // Seleccionar una ruta alternativa
  const selectAlternativeRoute = useCallback((index: number) => {
    if (index >= 0 && index < alternativeRoutes.length) {
      setSelectedRouteIndex(index);
      setRoute(alternativeRoutes[index]);
    }
  }, [alternativeRoutes]);

  const handleRecalculateRoute = useCallback(async () => {
    if (userLocation && endLocation.coords) {
      setStartLocation({ coords: userLocation, name: 'Mi ubicación' });
      setIsOffRoute(false);
      offRouteCounterRef.current = 0;
      return await handleCalculateRoute(userLocation, endLocation.coords);
    }
    return null;
  }, [userLocation, endLocation.coords, handleCalculateRoute]);

  // Detección de fuera de ruta y notificaciones
  useEffect(() => {
    if (!isRouteMode || !userLocation || !route || route.coordinates.length < 2 || isLoading) {
      setIsOffRoute(false);
      offRouteCounterRef.current = 0;
      return;
    }

    // Calcular la distancia mínima a CUALQUIER segmento de la ruta (más preciso que punto a punto)
    let minDistance = Infinity;

    // Iteramos por segmentos (i a i+1)
    for (let i = 0; i < route.coordinates.length - 1; i++) {
      const [lng1, lat1] = route.coordinates[i];
      const [lng2, lat2] = route.coordinates[i + 1];

      const dist = distanceToSegment(
        { lat: userLocation.lat, lng: userLocation.lng },
        { lat: lat1, lng: lng1 },
        { lat: lat2, lng: lng2 }
      );

      if (dist < minDistance) minDistance = dist;
    }

    // Umbral aumentado a 70m para ser más tolerante
    const isCurrentlyOff = minDistance > 70;

    if (isCurrentlyOff) {
      offRouteCounterRef.current += 1;
      console.log(`[Navigation] Off route check: ${offRouteCounterRef.current}/3 (Dist: ${Math.round(minDistance)}m)`);
    } else {
      offRouteCounterRef.current = 0;
      if (isOffRoute) setIsOffRoute(false); // Volvimos a la ruta
    }

    // Recálculo AUTOMÁTICO
    if (offRouteCounterRef.current >= 3 && !isLoading) {
      console.log('⚠️ Fuera de ruta confirmado. Recalculando automáticamente...');
      offRouteCounterRef.current = 0; // Resetear contador
      setIsOffRoute(true); // Activa flag visual momentáneo


      // Notificación de voz (es una alerta importante)
      speak('Recalculando ruta', true);

      sendNotification('Recalculando ruta...', {
        body: 'Te has desviado, buscando nueva ruta.',
        tag: 'recalc',
        silent: true // Para no molestar demasiado
      });

      handleRecalculateRoute().then(() => {
        setIsOffRoute(false);
      });
    }
  }, [userLocation, route, isRouteMode, isOffRoute, isLoading, handleRecalculateRoute]);

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

  // Copiar ETA al portapapeles
  const handleShareETA = useCallback(() => {
    if (!route) return null;
    const min = Math.round(route.duration / 60);
    const text = `Voy en camino. Llego en aprox ${min} minutos. 🚗`;
    navigator.clipboard.writeText(text);
    return text;
  }, [route]);

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
    alternativeRoutes,
    selectedRouteIndex,
    mlRecommendedIndex,
    selectAlternativeRoute,
    isRouteMode, setIsRouteMode,
    isOffRoute, setIsOffRoute,
    isLoading,
    handleCalculateRoute,
    handleRecalculateRoute,
    setAlternativeRoutes,
    handleShareETA
  };
};
