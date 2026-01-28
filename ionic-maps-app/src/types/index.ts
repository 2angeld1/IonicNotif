export interface LatLng {
  lat: number;
  lng: number;
}

export interface LocationSuggestion {
  display_name: string;
  lat: string;
  lon: string;
  place_id: string | number;
}

export interface RouteStep {
  instruction: string;
  distance: number;
  duration: number;
  name: string;
  location?: LatLng; // Coordenadas del paso para detección automática
  path?: LatLng[]; // Geometría detallada del paso
  traffic_status?: 'normal' | 'moderate' | 'heavy' | 'severe';
}

export interface RouteInfo {
  distance: number; // en metros
  duration: number; // en segundos (base)
  duration_in_traffic?: number; // en segundos (con tráfico)
  coordinates: [number, number][]; // [lng, lat]
  steps?: RouteStep[];
  isEstimate?: boolean;
  routeIndex?: number; // índice de la ruta alternativa
  summary?: string; // nombre/descripción de la ruta (ej: "Por Vía España")
  // Campos de predicción ML
  predicted_duration?: number; // Tiempo predicho por la IA
  ml_confidence?: number; // Confianza de la predicción (0-1)
  ml_recommended?: boolean; // Si es la ruta recomendada por la IA
  incidents_count?: number; // Número de incidentes en la ruta
}

export type FavoriteType = 'home' | 'work' | 'favorite' | 'other';

export interface FavoritePlace {
  id: string;
  name: string;
  location: LatLng;
  type: FavoriteType;
  address?: string;
  created_at: string;
}

export type VoiceMode = 'all' | 'alerts' | 'mute';

export interface UserSettings {
  voice_mode: VoiceMode;
}

// Convoy Types
export type ConvoyMemberStatus = 'online' | 'offline';

export interface ConvoyMember {
  user_id: string;
  name: string;
  location: LatLng;
  last_update: string;
  status: ConvoyMemberStatus;
}

export interface Convoy {
  _id: string;
  code: string;
  host_id: string;
  created_at: string;
  is_active: boolean;
  members: ConvoyMember[];
}
