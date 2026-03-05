import { useCallback } from 'react';
import type { LatLng, LocationSuggestion, FavoritePlace } from '../types';
import { searchLocations, getPlaceDetails, findNearbyPlaces, getPlaceDetailsExtended } from '../services/geocodingService';
import { getWeather, type IncidentType } from '../services/apiService';

interface UseAIChatHandlerProps {
  userLocation: LatLng | null;
  sLoc: { coords: LatLng | null; name: string };
  setSLoc: (loc: { coords: LatLng | null; name: string }) => void;
  setELoc: (loc: { coords: LatLng | null; name: string }) => void;
  setIsRouteModalOpen: (isOpen: boolean) => void;
  favorites: FavoritePlace[];
  setSearchResults: (results: LocationSuggestion[]) => void;
  setToast: (toast: { show: boolean; message: string }) => void;
  handleCreateIncident: (location: LatLng, type: IncidentType, description?: string) => Promise<any>;
  onAutoNavigate?: (location: LatLng, name: string, originCoords?: LatLng, originName?: string, waypoints?: LatLng[]) => void;
}

export const useAIChatHandler = ({
  userLocation,
  sLoc,
  setSLoc,
  setELoc,
  setIsRouteModalOpen,
  favorites,
  setSearchResults,
  setToast,
  handleCreateIncident,
  onAutoNavigate
}: UseAIChatHandlerProps) => {

  const handleAIChatNavigate = useCallback(async (dest: string | undefined, origin?: string, locations?: LatLng[]) => {
    console.log('🚀 [CHAT NAV] Iniciando con:', { dest, origin, locations });

    // Si tenemos una lista de localizaciones (multi-parada), el último es el destino
    let waypoints: LatLng[] | undefined = undefined;
    let finalDestCoords: LatLng | null = null;
    let finalDestName = dest || 'Destino';

    let originCoords: LatLng | null = null;
    let originName: string | undefined = undefined;

    if (locations && locations.length >= 2) {
      // Caso 1: [Origen, Parada1, ..., Destino] (mínimo 3 puntos)
      if (locations.length >= 3) {
        originCoords = locations[0];
        originName = 'Inicio';
        finalDestCoords = locations[locations.length - 1];
        waypoints = locations.slice(1, -1);
        console.log('📍 [CHAT NAV] Ruta Multi-punto completa:', { originCoords, waypoints, finalDestCoords });
      }
      // Caso 2: [Parada1, Destino] (2 puntos)
      else {
        finalDestCoords = locations[1];
        waypoints = [locations[0]];
        console.log('📍 [CHAT NAV] Parada y Destino detectados:', { waypoints, finalDestCoords });
      }
    } else if (locations && locations.length === 1) {
      finalDestCoords = locations[0];
    }

    // 1. Resolver el Origen (si no lo traemos ya resuelto de locations)
    if (!originCoords && origin) {
      const normalizedOrigin = origin.toLowerCase().replace('mi ', '').trim();
      let favStart = favorites.find(f => f.name.toLowerCase() === normalizedOrigin);
      if (!favStart) {
        if (normalizedOrigin.includes('casa') || normalizedOrigin.includes('hogar')) favStart = favorites.find(f => f.type === 'home');
        else if (normalizedOrigin.includes('trabajo') || normalizedOrigin.includes('oficina')) favStart = favorites.find(f => f.type === 'work');
      }

      if (favStart) {
        originCoords = favStart.location;
        originName = favStart.name;
        setSLoc({ coords: originCoords, name: originName });
      } else {
        const results = await searchLocations(origin, userLocation || undefined);
        if (results && results.length > 0) {
          originCoords = await getPlaceDetails(String(results[0].place_id));
          originName = results[0].display_name;
          setSLoc({ coords: originCoords, name: originName || '' });
        }
      }
    } else if (!originCoords && !sLoc.coords && userLocation) {
      originCoords = userLocation;
      originName = 'Tu Ubicación';
      setSLoc({ coords: originCoords, name: originName });
    } else if (!originCoords) {
      originCoords = sLoc.coords;
      originName = sLoc.name;
    }

    // 2. Resolver el Destino (si no lo traemos ya resuelto)
    if (finalDestCoords) {
      if (onAutoNavigate) {
        onAutoNavigate(finalDestCoords, finalDestName, originCoords || undefined, originName, waypoints);
      } else {
        setELoc({ coords: finalDestCoords, name: finalDestName });
        setIsRouteModalOpen(true);
      }
      return;
    }

    const safeDest = dest || '';
    const normalizedDest = safeDest.toLowerCase().replace('mi ', '').trim();

    let fav = favorites.find(f => f.name.toLowerCase() === normalizedDest);

    if (!fav) {
      if (normalizedDest.includes('casa') || normalizedDest.includes('hogar')) {
        fav = favorites.find(f => f.type === 'home');
      } else if (normalizedDest.includes('trabajo') || normalizedDest.includes('oficina')) {
        fav = favorites.find(f => f.type === 'work');
      }
    }

    if (fav) {
      console.log('⭐ [CHAT NAV] Destino Favorito:', fav.name, fav.location);
      if (onAutoNavigate) {
        onAutoNavigate(fav.location, fav.name, originCoords || undefined, originName);
      } else {
        setELoc({ coords: fav.location, name: fav.name });
        setToast({ show: true, message: `⭐ Destino: ${fav.name} (Favorito)` });
        setIsRouteModalOpen(true);
      }
      return;
    }

    try {
      const results = await searchLocations(safeDest, userLocation || undefined);
      if (results && results.length > 0) {
        const firstResult = results[0];
        const details = await getPlaceDetails(String(firstResult.place_id));
        const finalCoords = details || null;
        const finalName = firstResult.display_name;

        if (finalCoords && onAutoNavigate) {
          onAutoNavigate(finalCoords, finalName, originCoords || undefined, originName);
        } else {
          setELoc({ coords: finalCoords, name: finalName });
          setIsRouteModalOpen(true);
        }
      } else {
        setELoc({ coords: null, name: safeDest });
        setIsRouteModalOpen(true);
      }
    } catch (e) {
      setELoc({ coords: null, name: safeDest });
      setIsRouteModalOpen(true);
    }
  }, [userLocation, sLoc, favorites, setSLoc, setELoc, setIsRouteModalOpen, setToast, onAutoNavigate]);

  const handleAIChatSearch = useCallback(async (query: string, count: number) => {
    setToast({ show: true, message: `🔎 Buscando ${count} lugares...` });
    try {
      const results = await findNearbyPlaces(query, userLocation || undefined);

      if (results && results.length > 0) {
        const topResults = results.slice(0, count);
        setSearchResults(topResults);
        setToast({ show: true, message: `✅ Encontrados ${topResults.length} de ${count} solicitados` });
        return topResults;
      }
      return [];
    } catch (e) {
      console.error(e);
      setToast({ show: true, message: '❌ Error en la búsqueda' });
      return [];
    }
  }, [userLocation, setSearchResults, setToast]);

  const handleAIChatReportIncident = useCallback(async (type: string) => {
    if (!userLocation) {
      setToast({ show: true, message: '❌ Se necesita tu ubicación' });
      return;
    }
    // Mapeo seguro a IncidentType
    const validTypes: Record<string, IncidentType> = {
      'accident': 'accident',
      'police': 'police',
      'hazard': 'hazard',
      'road_work': 'road_work',
      'animal': 'animal'
    };

    const incidentType = validTypes[type] || 'hazard';

    await handleCreateIncident(userLocation, incidentType, 'Reportado por voz');
    setToast({ show: true, message: '✅ Incidente reportado' });
  }, [userLocation, handleCreateIncident, setToast]);

  const handleAIChatCheckWeather = useCallback(async (location: string): Promise<string> => {
    let coords = userLocation;
    let locationName = "tu ubicación";

    if (location !== 'current') {
      try {
        const results = await findNearbyPlaces(location); // Usamos findNearbyPlaces para obtener coords de ciudad
        if (results && results.length > 0) {
          coords = { lat: parseFloat(results[0].lat), lng: parseFloat(results[0].lon) };
          locationName = results[0].display_name.split(',')[0];
        } else {
          return `No encontré el lugar "${location}". 🤷‍♂️`;
        }
      } catch (e) {
        return "Error buscando la ciudad.";
      }
    }

    if (!coords) return "No tengo ubicación para el clima.";

    try {
      const weather = await getWeather(coords.lat, coords.lng);
      if (weather) {
        return `☁️ Clima en ${locationName}:\n🌡️ ${weather.temperature}°C\n💧 ${weather.humidity}% Humedad\n📝 ${weather.description}`;
      }
    } catch (e) { console.error(e); }

    return "No pude conectar con el servicio de clima. ⚠️";
  }, [userLocation]);

  const handleAIChatPlaceDetails = useCallback(async (placeName: string): Promise<string> => {
    try {
      const results = await findNearbyPlaces(placeName, userLocation || undefined);
      if (!results || results.length === 0) return `No encontré "${placeName}".`;

      const place = results[0];
      // Obtener detalles extendidos
      const details = await getPlaceDetailsExtended(String(place.place_id));

      if (details) {
        const status = details.opening_hours?.isOpen() ? "✅ Abierto ahora" : "🔴 Cerrado";
        const rating = details.rating ? `⭐ ${details.rating}/5` : "Sin calificación";
        const phone = details.formatted_phone_number || "Sin teléfono";

        return `🏢 **${details.name}**\n${rating}\n${status}\n📞 ${phone}\n📍 ${details.formatted_address}`;
      }

      return `Encontré ${place.display_name}, pero no tengo más detalles.`;
    } catch (e) {
      return "Error obteniendo información.";
    }
  }, [userLocation]);

  return {
    handleAIChatNavigate,
    handleAIChatSearch,
    handleAIChatReportIncident,
    handleAIChatCheckWeather,
    handleAIChatPlaceDetails
  };
};
