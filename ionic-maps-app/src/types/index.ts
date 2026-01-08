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
}

export interface RouteInfo {
  distance: number; // en metros
  duration: number; // en segundos
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
