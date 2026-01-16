export interface LatLng {
  lat: number;
  lng: number;
}

export interface LocationSuggestion {
  display_name: string;
  lat: string;
  lon: string;
  place_id: number;
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
