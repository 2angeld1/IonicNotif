import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import type { LatLng, RouteInfo, FavoritePlace } from '../types';
import type { Incident } from '../services/apiService';

// Íconos personalizados para los marcadores
const createIcon = (color: string) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        background-color: ${color};
        width: 30px;
        height: 30px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 3px solid white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
      ">
        <div style="
          width: 10px;
          height: 10px;
          background: white;
          border-radius: 50%;
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
        "></div>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 30],
  });
};

const startIcon = createIcon('#22c55e'); // Verde
const endIcon = createIcon('#ef4444'); // Rojo

// Icono para la ubicación del usuario normal (punto azul)
const defaultUserIcon = L.divIcon({
  className: 'user-location-marker',
  html: `
    <div style="position: relative; width: 24px; height: 24px;">
      <div style="
        position: absolute;
        width: 100%;
        height: 100%;
        background-color: rgba(59, 130, 246, 0.5);
        border-radius: 50%;
        animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
      "></div>
      <div style="
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 12px;
        height: 12px;
        background-color: #2563eb;
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 0 10px rgba(37, 99, 235, 0.5);
      "></div>
    </div>
    <style>
      @keyframes ping {
        0% { transform: scale(1); opacity: 1; }
        75%, 100% { transform: scale(2.5); opacity: 0; }
      }
    </style>
  `,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

// Icono de "Coche/Navegación" para Modo Ruta
const navIcon = L.divIcon({
  className: 'nav-marker',
  html: `
    <div style="
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
    ">
      <svg viewBox="0 0 24 24" fill="#3b82f6" style="width: 100%; height: 100%; transform: rotate(-45deg);">
        <path d="M12 2L4.5 20.29C4.21 21 4.95 21.74 5.66 21.45L12 19.03L18.34 21.45C19.05 21.74 19.79 21 19.5 20.29L12 2Z" stroke="white" stroke-width="2" stroke-linejoin="round"/>
      </svg>
    </div>
  `,
  iconSize: [40, 40],
  iconAnchor: [20, 20],
});

// Íconos para incidencias
const incidentIconConfig: Record<string, { color: string; emoji: string }> = {
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

const createIncidentIcon = (type: string) => {
  const config = incidentIconConfig[type] || incidentIconConfig.other;
  return L.divIcon({
    className: 'incident-marker',
    html: `
      <div style="
        background-color: ${config.color};
        width: 32px;
        height: 32px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
      ">
        ${config.emoji}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

// Íconos para lugares favoritos
const favoriteIconConfig: Record<string, { color: string; emoji: string }> = {
  home: { color: '#8b5cf6', emoji: '🏠' },
  work: { color: '#f59e0b', emoji: '🏢' },
  favorite: { color: '#ec4899', emoji: '⭐' },
  other: { color: '#6b7280', emoji: '📍' },
};

const createFavoriteIcon = (type: string) => {
  const config = favoriteIconConfig[type] || favoriteIconConfig.other;
  return L.divIcon({
    className: 'favorite-marker',
    html: `
      <div style="
        background-color: ${config.color};
        width: 32px;
        height: 32px;
        border-radius: 12px;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
      ">
        ${config.emoji}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

// Componente para centrar el mapa cuando cambian los puntos
const MapController: React.FC<{
  start: LatLng | null;
  end: LatLng | null;
  route: RouteInfo | null;
  userLocation?: LatLng | null;
  isRouteMode?: boolean;
}> = ({ start, end, route, userLocation, isRouteMode }) => {
  const map = useMap();

  useEffect(() => {
    // Forzar redimensionamiento del mapa después de un breve delay
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 100);

    return () => clearTimeout(timer);
  }, [map]);

  // Efecto para centrado inicial o cambio de ruta/puntos
  useEffect(() => {
    if (route && route.coordinates.length > 1) {
      const bounds = L.latLngBounds(
        route.coordinates.map(([lng, lat]) => [lat, lng] as [number, number])
      );
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (start && end) {
      const bounds = L.latLngBounds([[start.lat, start.lng], [end.lat, end.lng]]);
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (start && !route) {
      map.setView([start.lat, start.lng], 14);
    } else if (end && !route) {
      map.setView([end.lat, end.lng], 14);
    }
  }, [start, end, route, map]); // Eliminado userLocation e isRouteMode de aquí

  // Efecto separado para el modo navegación
  useEffect(() => {
    if (isRouteMode && userLocation) {
      map.setView([userLocation.lat, userLocation.lng], 17, {
        animate: true,
        duration: 1
      });
    }
  }, [isRouteMode, userLocation, map]);

  return null;
};

// Componente para capturar clicks en el mapa
const MapClickHandler: React.FC<{
  onMapClick?: (location: LatLng) => void;
}> = ({ onMapClick }) => {
  useMapEvents({
    click: (e) => {
      if (onMapClick) {
        onMapClick({ lat: e.latlng.lat, lng: e.latlng.lng });
      }
    },
  });
  return null;
};

interface MapViewProps {
  start: LatLng | null;
  end: LatLng | null;
  route: RouteInfo | null;
  incidents?: Incident[];
  favorites?: FavoritePlace[];
  userLocation?: LatLng | null;
  isRouteMode?: boolean; // Nueva prop
  onMapClick?: (location: LatLng) => void;
  onIncidentClick?: (incident: Incident) => void;
  onFavoriteClick?: (favorite: FavoritePlace) => void;
  onRecenterUser?: () => void;
}

const MapView: React.FC<MapViewProps> = ({ 
  start, 
  end, 
  route, 
  incidents = [],
  favorites = [],
  userLocation,
  isRouteMode,
  onMapClick,
  onIncidentClick,
  onFavoriteClick,
  onRecenterUser
}) => {
  // Forzar redimensionamiento cuando el componente se monta
  useEffect(() => {
    const timer = setTimeout(() => {
      if (mapRef.current) {
        mapRef.current.invalidateSize();
      }
    }, 200);

    // Listener para redimensionamiento de ventana
    const handleResize = () => {
      if (mapRef.current) {
        mapRef.current.invalidateSize();
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  const mapRef = useRef<L.Map>(null);

  // Centro por defecto (Ciudad de Panamá)
  const defaultCenter: [number, number] = [8.9824, -79.5199];

  // Convertir coordenadas de la ruta [lng, lat] a [lat, lng] para Leaflet
  const routePositions: [number, number][] = route
    ? route.coordinates.map(([lng, lat]) => [lat, lng])
    : [];

  return (
    <div className={`w-full h-full relative transition-all duration-700 ease-in-out ${isRouteMode ? 'perspective-active' : ''}`}>
      <MapContainer
        center={defaultCenter}
        zoom={13}
        className="w-full h-full z-0 transition-transform duration-700 ease-in-out"
        ref={mapRef}
        zoomControl={!isRouteMode}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={isRouteMode
            ? "https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
            : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"}
        />

        <MapController
          start={start}
          end={end}
          route={route}
          userLocation={userLocation}
          isRouteMode={isRouteMode}
        />

        {/* Handler para clicks en el mapa */}
        <MapClickHandler onMapClick={onMapClick} />

        {start && !favorites.some(f => f.location.lat === start.lat && f.location.lng === start.lng) && (
          <Marker position={[start.lat, start.lng]} icon={startIcon} />
        )}

        {end && !favorites.some(f => f.location.lat === end.lat && f.location.lng === end.lng) && (
          <Marker position={[end.lat, end.lng]} icon={endIcon} />
        )}

        {routePositions.length > 1 && (
          <>
            {/* Sombra de la ruta */}
            <Polyline
              positions={routePositions}
              pathOptions={{
                color: '#1e40af',
                weight: 8,
                opacity: 0.3,
              }}
            />
            {/* Ruta principal */}
            <Polyline
              positions={routePositions}
              pathOptions={{
                color: '#3b82f6',
                weight: 5,
                opacity: 1,
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />
          </>
        )}

        {/* Marcadores de incidencias */}
        {incidents.map((incident, idx) => {
          const key = incident.id || `${incident.location.lat}-${incident.location.lng}-${idx}`;
          return (
            <Marker
              key={key}
              position={[incident.location.lat, incident.location.lng]}
              icon={createIncidentIcon(incident.type)}
              eventHandlers={{
                click: () => onIncidentClick?.(incident),
              }}
            />
          );
        })}

        {/* Marcadores de lugares favoritos */}
        {favorites?.map((fav) => (
          <Marker
            key={fav.id}
            position={[fav.location.lat, fav.location.lng]}
            icon={createFavoriteIcon(fav.type)}
            eventHandlers={{
              click: () => onFavoriteClick?.(fav),
            }}
          />
        ))}

        {/* Marcador de ubicación del usuario */}
        {userLocation && (
          <Marker
            position={[userLocation.lat, userLocation.lng]}
            icon={isRouteMode ? navIcon : defaultUserIcon}
            zIndexOffset={1000} // Siempre encima
          />
        )}
      </MapContainer>

      {/* Botón flotante para recentrar en usuario (Estilo unificado con el de alertas) */}
      {userLocation && !isRouteMode && (
        <div style={{ position: 'absolute', bottom: '82px', right: '10px', zIndex: 1000 }}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              mapRef.current?.setView([userLocation.lat, userLocation.lng], 15);
              onRecenterUser?.();
            }}
            style={{ borderRadius: '50%' }}
            className="w-14 h-14 bg-white shadow-lg flex items-center justify-center text-blue-600 hover:bg-gray-50 transition-all active:scale-95 border border-gray-200"
            title="Mi Ubicación"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      )}

      <style>{`
        .perspective-active {
          perspective: 1000px;
          overflow: hidden;
          background-color: #e5e7eb;
        }
        .perspective-active .leaflet-container {
          transform: rotateX(25deg) scale(2.0); /* Menor rotación, mayor escala */
          transform-origin: center 50%; /* Pivot central */
          height: 100% !important; 
        }
        .perspective-active .leaflet-marker-icon {
          filter: drop-shadow(0 10px 10px rgba(0,0,0,0.3));
        }
      `}</style>
    </div>
  );
};

export default MapView;
