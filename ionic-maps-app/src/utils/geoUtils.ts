

import { 
  arrowForwardOutline,
  arrowUpOutline,
  returnUpBackOutline,
  returnUpForwardOutline,
  locationOutline
} from 'ionicons/icons';

export const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
  const R = 6371000; // Radio de la Tierra en metros
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};

export const formatDistance = (meters: number): string => {
  if (meters >= 1000) return `${(meters / 1000).toFixed(1)} km`;
  return `${Math.round(meters)} m`;
};

export const formatDuration = (seconds: number): string => {
  if (seconds === 0) return 'N/A';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}min`;
  return `${minutes} min`;
};

export const getManeuverIcon = (instruction: string): string => {
  const lower = instruction.toLowerCase();
  if (lower.includes('derecha') || lower.includes('right')) return returnUpForwardOutline;
  if (lower.includes('izquierda') || lower.includes('left')) return returnUpBackOutline;
  if (lower.includes('recto') || lower.includes('straight') || lower.includes('continúa') || lower.includes('continue')) return arrowUpOutline;
  if (lower.includes('destino') || lower.includes('llegada') || lower.includes('destination')) return locationOutline;
  return arrowForwardOutline;
};
