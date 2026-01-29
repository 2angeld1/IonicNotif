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
  onAutoNavigate?: (location: LatLng, name: string) => void;
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

  const handleAIChatNavigate = useCallback(async (dest: string) => {
    if (!sLoc.coords && userLocation) {
      setSLoc({ coords: userLocation, name: 'Tu Ubicación' });
    }

    const normalizedDest = dest.toLowerCase().replace('mi ', '').trim();

    // Búsqueda inteligente en favoritos (por nombre o por TIPO)
    let fav = favorites.find(f => f.name.toLowerCase() === normalizedDest);

    // Si no encuentra por nombre exacto, buscar por tipo
    if (!fav) {
      if (normalizedDest.includes('casa') || normalizedDest.includes('hogar')) {
        fav = favorites.find(f => f.type === 'home');
      } else if (normalizedDest.includes('trabajo') || normalizedDest.includes('oficina')) {
        fav = favorites.find(f => f.type === 'work');
      }
    }

    if (fav) {
      if (onAutoNavigate) {
        onAutoNavigate(fav.location, fav.name);
      } else {
        setELoc({ coords: fav.location, name: fav.name });
        setToast({ show: true, message: `⭐ Destino: ${fav.name} (Favorito)` });
        setIsRouteModalOpen(true);
      }
      return;
    }

    try {
      const results = await searchLocations(dest, userLocation || undefined);
      if (results && results.length > 0) {
        const firstResult = results[0];
        const details = await getPlaceDetails(String(firstResult.place_id));
        if (details) {
          setELoc({ coords: details, name: firstResult.display_name });
        } else {
          setELoc({ coords: null, name: firstResult.display_name });
        }
      } else {
        setELoc({ coords: null, name: dest });
      }
    } catch (e) {
      setELoc({ coords: null, name: dest });
    }

    setIsRouteModalOpen(true);
  }, [userLocation, sLoc.coords, favorites, setSLoc, setELoc, setIsRouteModalOpen, setToast]);

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
          } catch(e) {
              return "Error buscando la ciudad.";
          }
      }

      if (!coords) return "No tengo ubicación para el clima.";

      try {
        const weather = await getWeather(coords.lat, coords.lng);
        if (weather) {
            return `☁️ Clima en ${locationName}:\n🌡️ ${weather.temperature}°C\n💧 ${weather.humidity}% Humedad\n📝 ${weather.description}`;
        }
      } catch(e) { console.error(e); }
      
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
