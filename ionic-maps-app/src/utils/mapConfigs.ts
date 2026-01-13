export const incidentIconConfig: Record<string, { color: string; emoji: string }> = {
  accident: { color: '#dc2626', emoji: '🚗' },
  road_work: { color: '#ea580c', emoji: '🚧' },
  hazard: { color: '#ca8a04', emoji: '⚠️' },
  animal: { color: '#16a34a', emoji: '🐕' },
  police: { color: '#2563eb', emoji: '👮' },
  flood: { color: '#0891b2', emoji: '🌊' },
  closed_road: { color: '#4b5563', emoji: '🚫' },
  slow_traffic: { color: '#d97706', emoji: '🐌' },
  other: { color: '#7c3aed', emoji: '📍' },
};

export const favoriteIconConfig: Record<string, { color: string; emoji: string }> = {
  home: { color: '#8b5cf6', emoji: '🏠' },
  work: { color: '#f59e0b', emoji: '🏢' },
  favorite: { color: '#ec4899', emoji: '⭐' },
  other: { color: '#6b7280', emoji: '📍' },
};

export const mapConfig = {
  mapId: "90f87356969d889c", // ID de demo vectorial que soporta 3D/Tilt
  defaultCenter: { lat: 8.9824, lng: -79.5199 },
  defaultZoom: 13,
};
