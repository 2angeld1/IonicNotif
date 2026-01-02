import axios from 'axios';
import type { LocationSuggestion, RouteInfo } from '../types';

const NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org';
// OSRM Demo Server - Gratuito y traza rutas reales sobre calles
const OSRM_BASE_URL = 'https://router.project-osrm.org';

/**
 * Buscar ubicaciones por texto usando Nominatim (OpenStreetMap)
 */
export const searchLocations = async (query: string): Promise<LocationSuggestion[]> => {
  if (!query || query.length < 3) return [];
  
  try {
    const response = await axios.get(`${NOMINATIM_BASE_URL}/search`, {
      params: {
        q: query,
        format: 'json',
        limit: 8,
        addressdetails: 1,
        dedupe: 1,
        'accept-language': 'es',
      },
      headers: {
        'User-Agent': 'IonicMapsApp/1.0',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error buscando ubicaciones:', error);
    return [];
  }
};

/**
 * Obtener la ruta entre dos puntos usando OSRM (rutas reales sobre calles)
 */
export const getRoute = async (
  start: { lat: number; lng: number },
  end: { lat: number; lng: number }
): Promise<RouteInfo | null> => {
  try {
    // OSRM usa formato: /route/v1/{profile}/{coordinates}
    // coordinates: lng,lat;lng,lat
    const coordinates = `${start.lng},${start.lat};${end.lng},${end.lat}`;
    
    const response = await axios.get(
      `${OSRM_BASE_URL}/route/v1/driving/${coordinates}`,
      {
        params: {
          overview: 'full',
          geometries: 'geojson',
          steps: true,
        },
      }
    );

    if (response.data.code !== 'Ok' || !response.data.routes.length) {
      throw new Error('No se encontró ruta');
    }

    const route = response.data.routes[0];
    const { distance, duration } = route;
    // OSRM devuelve coordenadas en formato [lng, lat]
    const coordinates_route = route.geometry.coordinates;

    return {
      distance,
      duration,
      coordinates: coordinates_route,
    };
  } catch (error) {
    console.error('Error obteniendo ruta:', error);
    // Fallback: línea directa si falla
    return {
      distance: calculateDirectDistance(start, end),
      duration: 0,
      coordinates: [
        [start.lng, start.lat],
        [end.lng, end.lat],
      ],
      isEstimate: true,
    };
  }
};

/**
 * Calcular distancia directa entre dos puntos (fórmula Haversine)
 */
const calculateDirectDistance = (
  start: { lat: number; lng: number },
  end: { lat: number; lng: number }
): number => {
  const R = 6371000; // Radio de la Tierra en metros
  const dLat = ((end.lat - start.lat) * Math.PI) / 180;
  const dLon = ((end.lng - start.lng) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((start.lat * Math.PI) / 180) *
      Math.cos((end.lat * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

/**
 * Geocodificación inversa - obtener dirección desde coordenadas
 */
export const reverseGeocode = async (lat: number, lng: number): Promise<string> => {
  try {
    const response = await axios.get(`${NOMINATIM_BASE_URL}/reverse`, {
      params: {
        lat,
        lon: lng,
        format: 'json',
      },
      headers: {
        'Accept-Language': 'es',
      },
    });
    return response.data.display_name || 'Ubicación desconocida';
  } catch (error) {
    console.error('Error en geocodificación inversa:', error);
    return 'Ubicación desconocida';
  }
};
