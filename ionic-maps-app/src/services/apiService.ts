import axios from 'axios';
import type { LatLng, RouteInfo, FavoritePlace, FavoriteType } from '../types';

// URL del backend FastAPI
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});



// ============== LUGARES FAVORITOS ==============
export const getFavorites = async (): Promise<FavoritePlace[]> => {
  try {
    const response = await api.get('/favorites/');
    const raws = response.data || [];
    return raws.map((raw: any) => {
      const rawId = raw.id ?? raw._id;
      let id = '';
      if (rawId) {
        id = typeof rawId === 'string' ? rawId : rawId.$oid || String(rawId);
      }
      return {
        ...raw,
        id,
      } as FavoritePlace;
    });
  } catch (error) {
    console.error('Error obteniendo favoritos:', error);
    return [];
  }
};

export const addFavorite = async (favorite: {
  name: string;
  location: LatLng;
  type: FavoriteType;
  address?: string;
}): Promise<FavoritePlace | null> => {
  try {
    const response = await api.post('/favorites/', favorite);
    const raw = response.data;
    const rawId = raw.id ?? raw._id;
    let id = '';
    if (rawId) {
      id = typeof rawId === 'string' ? rawId : rawId.$oid || String(rawId);
    }
    return { ...raw, id } as FavoritePlace;
  } catch (error) {
    console.error('Error guardando favorito:', error);
    return null;
  }
};

export const deleteFavorite = async (id: string): Promise<boolean> => {
  try {
    await api.delete(`/favorites/${id}`);
    return true;
  } catch (error) {
    console.error('Error eliminando favorito:', error);
    return false;
  }
};

// ============== TIPOS ==============
export interface WeatherInfo {
  condition: string;
  temperature: number;
  humidity: number;
  visibility: number;
  wind_speed: number;
  description: string;
}

export interface Incident {
  id: string;
  location: LatLng;
  type: IncidentType;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description?: string;
  created_at: string;
  expires_at: string;
  confirmations: number;
  is_active: boolean;
}

export type IncidentType =
  | 'accident'
  | 'road_work'
  | 'hazard'
  | 'animal'
  | 'police'
  | 'flood'
  | 'closed_road'
  | 'slow_traffic'
  | 'other';

export interface IncidentTypeInfo {
  value: IncidentType;
  label: string;
  icon: string;
}

export interface RouteWithPrediction extends RouteInfo {
  predicted_duration: number;
  weather?: WeatherInfo;
  incidents_on_route: Incident[];
  confidence: number;
  factors: Record<string, number>;
}

export interface TripData {
  start: LatLng;
  end: LatLng;
  start_name?: string;
  end_name?: string;
  distance: number;
  estimated_duration: number;
  actual_duration: number;
}

// ============== RUTAS ==============
export const calculateRouteWithML = async (
  start: LatLng,
  end: LatLng,
  startName?: string,
  endName?: string
): Promise<RouteWithPrediction | null> => {
  try {
    const response = await api.post('/routes/calculate', {
      start,
      end,
      start_name: startName,
      end_name: endName,
    });
    return response.data;
  } catch (error) {
    console.error('Error calculando ruta con ML:', error);
    return null;
  }
};

export const getAlternativeRoutes = async (
  start: LatLng,
  end: LatLng
): Promise<{ weather: WeatherInfo; alternatives: RouteWithPrediction[]; recommended_index: number } | null> => {
  try {
    const response = await api.post('/routes/alternatives', { start, end });
    return response.data;
  } catch (error) {
    console.error('Error obteniendo rutas alternativas:', error);
    return null;
  }
};

// ============== INCIDENCIAS ==============
export const createIncident = async (
  location: LatLng,
  type: IncidentType,
  severity: 'low' | 'medium' | 'high' | 'critical' = 'medium',
  description?: string,
  expiresInMinutes: number = 60
): Promise<Incident | null> => {
  try {
    const response = await api.post('/incidents/', {
      location,
      type,
      severity,
      description,
      expires_in_minutes: expiresInMinutes,
    });
    const raw = response.data;
    // Normalizar campo id (backend puede devolver _id como objeto {$oid} o string)
    const rawId = raw.id ?? raw._id;
    let id = '';
    if (rawId) {
      id = typeof rawId === 'string' ? rawId : rawId.$oid || String(rawId);
    }
    return {
      id,
      location: raw.location,
      type: raw.type,
      severity: raw.severity,
      description: raw.description,
      created_at: raw.created_at?.$date || raw.created_at || '',
      expires_at: raw.expires_at?.$date || raw.expires_at || '',
      confirmations: raw.confirmations || 0,
      is_active: raw.is_active ?? true,
    } as Incident;
  } catch (error) {
    console.error('Error creando incidencia:', error);
    return null;
  }
};

export const getIncidents = async (
  lat?: number,
  lng?: number,
  radiusKm: number = 10
): Promise<Incident[]> => {
  try {
    const params: Record<string, number> = { radius_km: radiusKm };
    if (lat !== undefined && lng !== undefined) {
      params.lat = lat;
      params.lng = lng;
    }
    const response = await api.get('/incidents/', { params });
      const raws = response.data || [];
      // Normalizar cada incidencia para garantizar `id` y strings en fechas
      const incidents: Incident[] = raws.map((raw: any) => {
        const rawId = raw.id ?? raw._id;
        let id = '';
        if (rawId) {
          id = typeof rawId === 'string' ? rawId : rawId.$oid || String(rawId);
        }
        return {
          id,
          location: raw.location,
          type: raw.type,
          severity: raw.severity,
          description: raw.description,
          created_at: raw.created_at?.$date || raw.created_at || '',
          expires_at: raw.expires_at?.$date || raw.expires_at || '',
          confirmations: raw.confirmations || 0,
          is_active: raw.is_active ?? true,
        } as Incident;
      });
      return incidents;
  } catch (error) {
    console.error('Error obteniendo incidencias:', error);
    return [];
  }
};

export const getIncidentTypes = async (): Promise<IncidentTypeInfo[]> => {
  try {
    const response = await api.get('/incidents/types');
    return response.data.types;
  } catch (error) {
    console.error('Error obteniendo tipos de incidencias:', error);
    return [];
  }
};

export const confirmIncident = async (incidentId: string): Promise<boolean> => {
  try {
    await api.post(`/incidents/${incidentId}/confirm`);
    return true;
  } catch (error) {
    console.error('Error confirmando incidencia:', error);
    return false;
  }
};

export const dismissIncident = async (incidentId: string): Promise<boolean> => {
  try {
    await api.post(`/incidents/${incidentId}/dismiss`);
    return true;
  } catch (error) {
    console.error('Error descartando incidencia:', error);
    return false;
  }
};

// ============== VIAJES (ML Training) ==============
export const saveTrip = async (trip: TripData): Promise<boolean> => {
  try {
    await api.post('/trips/', trip);
    return true;
  } catch (error) {
    console.error('Error guardando viaje:', error);
    return false;
  }
};

export const getTripsCount = async (): Promise<{
  count: number;
  ready_for_training: boolean;
  message: string;
}> => {
  try {
    const response = await api.get('/trips/count');
    return response.data;
  } catch (error) {
    console.error('Error obteniendo cantidad de viajes:', error);
    return { count: 0, ready_for_training: false, message: 'Error de conexión' };
  }
};

export const trainModel = async (): Promise<{
  success: boolean;
  message: string;
  mae?: number;
  feature_importance?: Record<string, number>;
}> => {
  try {
    const response = await api.post('/trips/train');
    return response.data;
  } catch (error: unknown) {
    const axiosError = error as { response?: { data?: { detail?: string } } };
    return {
      success: false,
      message: axiosError.response?.data?.detail || 'Error entrenando modelo',
    };
  }
};

export const getModelStatus = async (): Promise<{
  is_trained: boolean;
  trips_count: number;
  ready_for_training: boolean;
  using_heuristics: boolean;
  message: string;
}> => {
  try {
    const response = await api.get('/trips/model-status');
    return response.data;
  } catch (error) {
    console.error('Error obteniendo estado del modelo:', error);
    return {
      is_trained: false,
      trips_count: 0,
      ready_for_training: false,
      using_heuristics: true,
      message: 'Error de conexión',
    };
  }
};

// ============== CLIMA ==============
export const getWeather = async (lat: number, lng: number): Promise<WeatherInfo | null> => {
  try {
    const response = await api.get('/weather/', { params: { lat, lng } });
    return response.data;
  } catch (error) {
    console.error('Error obteniendo clima:', error);
    return null;
  }
};

// ============== HEALTH ==============
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await api.get('/health');
    return response.data.status === 'healthy';
  } catch (error) {
    console.error('API no disponible:', error);
    return false;
  }
};
