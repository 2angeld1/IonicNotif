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

export interface RouteInfo {
  distance: number; // en metros
  duration: number; // en segundos
  coordinates: [number, number][]; // [lng, lat]
  isEstimate?: boolean;
}
