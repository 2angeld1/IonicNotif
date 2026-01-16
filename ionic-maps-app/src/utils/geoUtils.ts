
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

/**
 * Calcula la distancia más corta de un punto (P) a un segmento de línea (A-B).
 * Retorna la distancia en metros.
 */
export const distanceToSegment = (
  p: { lat: number; lng: number },
  a: { lat: number; lng: number },
  b: { lat: number; lng: number }
): number => {
  const x = p.lng;
  const y = p.lat;
  const x1 = a.lng;
  const y1 = a.lat;
  const x2 = b.lng;
  const y2 = b.lat;

  const A = x - x1;
  const B = y - y1;
  const C = x2 - x1;
  const D = y2 - y1;

  const dot = A * C + B * D;
  const lenSq = C * C + D * D;

  // Si lenSq es 0, los puntos A y B son iguales
  let param = -1;
  if (lenSq !== 0) {
    param = dot / lenSq;
  }

  let xx, yy;

  if (param < 0) {
    xx = x1;
    yy = y1;
  } else if (param > 1) {
    xx = x2;
    yy = y2;
  } else {
    xx = x1 + param * C;
    yy = y1 + param * D;
  }

  // Ahora calculamos la distancia entre (x,y) y el punto proyectado (xx,yy)
  return calculateDistance(y, x, yy, xx);
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

/**
 * Calcula el bearing (dirección en grados) entre dos puntos
 * 0° = Norte, 90° = Este, 180° = Sur, 270° = Oeste
 */
export const calculateBearing = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
  const toRad = (deg: number) => deg * Math.PI / 180;
  const toDeg = (rad: number) => rad * 180 / Math.PI;

  const dLng = toRad(lng2 - lng1);
  const lat1Rad = toRad(lat1);
  const lat2Rad = toRad(lat2);

  const x = Math.sin(dLng) * Math.cos(lat2Rad);
  const y = Math.cos(lat1Rad) * Math.sin(lat2Rad) - Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLng);

  const bearing = toDeg(Math.atan2(x, y));
  return (bearing + 360) % 360; // Normalizar a 0-360
};

/**
 * Encuentra el punto más cercano en la ruta y calcula el heading hacia el siguiente punto
 */
export const calculateRouteHeading = (
  userLat: number,
  userLng: number,
  routeCoords: [number, number][] // [lng, lat][]
): number | null => {
  if (!routeCoords || routeCoords.length < 2) return null;

  let closestIndex = 0;
  let minDistance = Infinity;

  // Encontrar el punto más cercano en la ruta
  for (let i = 0; i < routeCoords.length; i++) {
    const [lng, lat] = routeCoords[i];
    const dist = calculateDistance(userLat, userLng, lat, lng);
    if (dist < minDistance) {
      minDistance = dist;
      closestIndex = i;
    }
  }

  // Buscar el siguiente punto en la ruta (adelante del usuario)
  // Usamos el siguiente punto o el que esté al menos 20m adelante
  let nextIndex = closestIndex + 1;
  while (nextIndex < routeCoords.length - 1) {
    const [lng, lat] = routeCoords[nextIndex];
    const dist = calculateDistance(userLat, userLng, lat, lng);
    if (dist > 20) break; // Al menos 20m adelante
    nextIndex++;
  }

  if (nextIndex >= routeCoords.length) {
    nextIndex = routeCoords.length - 1;
  }

  const [nextLng, nextLat] = routeCoords[nextIndex];
  return calculateBearing(userLat, userLng, nextLat, nextLng);
};

/**
 * Interpola suavemente entre dos conjuntos de coordenadas
 */
export const interpolatePosition = (
  current: { lat: number; lng: number },
  target: { lat: number; lng: number },
  factor: number = 0.15 // Factor de suavizado (0-1), menor = más suave
): { lat: number; lng: number } => {
  return {
    lat: current.lat + (target.lat - current.lat) * factor,
    lng: current.lng + (target.lng - current.lng) * factor,
  };
};

/**
 * Interpola suavemente un ángulo (heading) considerando el wrap-around de 360°
 */
export const interpolateHeading = (current: number, target: number, factor: number = 0.1): number => {
  let diff = target - current;

  // Manejar el wrap-around de 360 grados
  if (diff > 180) diff -= 360;
  if (diff < -180) diff += 360;

  return (current + diff * factor + 360) % 360;
};
