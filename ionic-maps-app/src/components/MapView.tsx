import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import type { LatLng, RouteInfo } from '../types';
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

// Icono para la ubicación del usuario (punto azul con pulsación)
const userLocationIcon = L.divIcon({
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

// Componente para centrar el mapa cuando cambian los puntos
const MapController: React.FC<{
  start: LatLng | null;
  end: LatLng | null;
  route: RouteInfo | null;
}> = ({ start, end, route }) => {
  const map = useMap();

  useEffect(() => {
    // Forzar redimensionamiento del mapa después de un breve delay
    // para asegurar que el contenedor tenga el tamaño correcto
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 100);

    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    if (route && route.coordinates.length > 1) {
      // Ajustar vista a la ruta completa
      const bounds = L.latLngBounds(
        route.coordinates.map(([lng, lat]) => [lat, lng] as [number, number])
      );
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (start && end) {
      const bounds = L.latLngBounds([
        [start.lat, start.lng],
        [end.lat, end.lng],
      ]);
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (start) {
      map.setView([start.lat, start.lng], 14);
    } else if (end) {
      map.setView([end.lat, end.lng], 14);
    }
  }, [start, end, route, map]);

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
  userLocation?: LatLng | null; // Nueva prop
  onMapClick?: (location: LatLng) => void;
  onIncidentClick?: (incident: Incident) => void;
  onRecenterUser?: () => void; // Callboack para recentrar
}

const MapView: React.FC<MapViewProps> = ({ 
  start, 
  end, 
  route, 
  incidents = [],
  userLocation,
  onMapClick,
  onIncidentClick,
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
    <MapContainer
      center={defaultCenter}
      zoom={13}
      className="w-full h-full"
      ref={mapRef}
      zoomControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      <MapController start={start} end={end} route={route} />
      
      {/* Handler para clicks en el mapa */}
      <MapClickHandler onMapClick={onMapClick} />
      
      {start && (
        <Marker position={[start.lat, start.lng]} icon={startIcon} />
      )}
      
      {end && (
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

      {/* Marcador de ubicación del usuario */}
      {userLocation && (
        <Marker
          position={[userLocation.lat, userLocation.lng]}
          icon={userLocationIcon}
          zIndexOffset={1000} // Siempre encima
        />
      )}

      {/* Botón flotante para recentrar en usuario */}
      {userLocation && (
        <div style={{ position: 'absolute', bottom: '20px', right: '20px', zIndex: 1000 }}>
          <button
            onClick={(e) => {
              e.stopPropagation(); // Evitar click en mapa
              mapRef.current?.setView([userLocation.lat, userLocation.lng], 15);
              onRecenterUser?.();
            }}
            className="bg-white p-3 rounded-full shadow-lg border border-gray-200 text-blue-600 hover:bg-gray-50 transition-colors"
            title="Mi Ubicación"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      )}
    </MapContainer>
  );
};

export default MapView;
