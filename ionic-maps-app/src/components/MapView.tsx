import React, { useEffect, useRef, useMemo } from 'react';
import { Map, AdvancedMarker, useMap } from '@vis.gl/react-google-maps';
import type { LatLng, RouteInfo, FavoritePlace } from '../types';
import type { Incident } from '../services/apiService';
import { useMapController } from '../hooks/useMapController';
import { incidentIconConfig, favoriteIconConfig, mapConfig } from '../utils/mapConfigs';

// Sub-componente para la Polilínea
const Polyline = (props: { points: google.maps.LatLngLiteral[], options?: google.maps.PolylineOptions }) => {
  const map = useMap();
  const polylineRef = useRef<google.maps.Polyline | null>(null);

  useEffect(() => {
    if (!map) return;
    polylineRef.current = new google.maps.Polyline({
      ...props.options,
      path: props.points,
      map: map,
    });
    return () => {
      if (polylineRef.current) polylineRef.current.setMap(null);
    };
  }, [map, props.points, props.options]);

  return null;
};

// Sub-componente para la Capa de Tráfico
const TrafficLayer = ({ visible }: { visible: boolean }) => {
  const map = useMap();
  const trafficLayerRef = useRef<google.maps.TrafficLayer | null>(null);

  useEffect(() => {
    if (!map) return;

    if (visible && !trafficLayerRef.current) {
      trafficLayerRef.current = new google.maps.TrafficLayer();
      trafficLayerRef.current.setMap(map);
    } else if (!visible && trafficLayerRef.current) {
      trafficLayerRef.current.setMap(null);
      trafficLayerRef.current = null;
    }

    return () => {
      if (trafficLayerRef.current) {
        trafficLayerRef.current.setMap(null);
        trafficLayerRef.current = null;
      }
    };
  }, [map, visible]);

  return null;
};

// Hook interno para centrar el mapa (usando el hook extraído)
const MapInstanceController: React.FC<any> = (props) => {
  useMapController(props.start, props.end, props.route, props.userLocation, props.isRouteMode, props.userHeading);
  return null;
};

interface MapViewProps {
  start: LatLng | null;
  end: LatLng | null;
  route: RouteInfo | null;
  incidents?: Incident[];
  favorites?: FavoritePlace[];
  userLocation?: LatLng | null;
  userHeading?: number | null;
  isRouteMode?: boolean;
  onMapClick?: (location: LatLng) => void;
  onIncidentClick?: (incident: Incident) => void;
  onFavoriteClick?: (favorite: FavoritePlace) => void;
}

const MapView: React.FC<MapViewProps> = ({
  start, end, route, incidents = [], favorites = [],
  userLocation, userHeading, isRouteMode,
  onMapClick, onIncidentClick, onFavoriteClick
}) => {
  const routePositions = useMemo(() => {
    return route ? route.coordinates.map(([lng, lat]) => ({ lat, lng })) : [];
  }, [route]);

  const renderCustomMarker = (color: string) => (
    <div className="w-[30px] h-[30px] rounded-full border-[3px] border-white shadow-lg flex items-center justify-center relative" style={{ backgroundColor: color }}>
      <div className="w-[10px] h-[10px] bg-white rounded-full"></div>
    </div>
  );

  return (
    <div className="w-full h-full relative touch-none">
      <Map
        mapId={mapConfig.mapId}
        defaultCenter={mapConfig.defaultCenter}
        defaultZoom={mapConfig.defaultZoom}
        className="w-full h-full z-0"
        disableDefaultUI={true}
        gestureHandling={'greedy'}
        onClick={(e) => {
          if (onMapClick && e.detail.latLng) {
            onMapClick({ lat: e.detail.latLng.lat, lng: e.detail.latLng.lng });
          }
        }}
      >
        <MapInstanceController
          start={start} end={end} route={route}
          userLocation={userLocation} isRouteMode={isRouteMode}
          userHeading={userHeading}
        />

        {/* Capa de Tráfico - visible cuando hay ruta */}
        <TrafficLayer visible={!!route} />

        {/* Marcadores de Inicio/Fin */}
        {start && !favorites.some(f => f.location.lat === start.lat && f.location.lng === start.lng) && (
          <AdvancedMarker position={start}>{renderCustomMarker('#22c55e')}</AdvancedMarker>
        )}
        {end && !favorites.some(f => f.location.lat === end.lat && f.location.lng === end.lng) && (
          <AdvancedMarker position={end}>{renderCustomMarker('#ef4444')}</AdvancedMarker>
        )}

        {/* Polilíneas de Ruta */}
        {routePositions.length > 1 && (
          <>
            <Polyline points={routePositions} options={{ strokeColor: '#1e40af', strokeOpacity: 0.3, strokeWeight: 8 }} />
            <Polyline points={routePositions} options={{ strokeColor: '#3b82f6', strokeOpacity: 1, strokeWeight: 5 }} />
          </>
        )}

        {/* Incidencias */}
        {incidents.map((incident, idx) => {
          const config = incidentIconConfig[incident.type] || incidentIconConfig.other;
          return (
            <AdvancedMarker
              key={incident.id || idx}
              position={incident.location}
              onClick={() => onIncidentClick?.(incident)}
            >
              <div
                className="w-8 h-8 rounded-full border-[3px] border-white shadow-md flex items-center justify-center text-sm"
                style={{ backgroundColor: config.color }}
              >
                {config.emoji}
              </div>
            </AdvancedMarker>
          );
        })}

        {/* Favoritos */}
        {favorites.map((fav) => {
          const config = favoriteIconConfig[fav.type] || favoriteIconConfig.other;
          return (
            <AdvancedMarker key={fav.id} position={fav.location} onClick={() => onFavoriteClick?.(fav)}>
              <div
                className="w-8 h-8 rounded-xl border-[3px] border-white shadow-md flex items-center justify-center text-sm"
                style={{ backgroundColor: config.color }}
              >
                {config.emoji}
              </div>
            </AdvancedMarker>
          );
        })}

        {/* Ubicación del Usuario con Flecha de Navegación */}
        {userLocation && (
          <AdvancedMarker position={userLocation} zIndex={1000}>
            {isRouteMode ? (
              // En modo navegación: puntero fijo hacia arriba (la cámara rota, no el puntero)
              <div
                className="w-14 h-14 flex items-center justify-center"
                style={{
                  filter: 'drop-shadow(0 6px 12px rgba(0,0,0,0.5))',
                }}
              >
                <svg viewBox="0 0 24 24" className="w-full h-full">
                  <defs>
                    <linearGradient id="navGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="#4285F4" />
                      <stop offset="100%" stopColor="#1a73e8" />
                    </linearGradient>
                    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                      <feGaussianBlur stdDeviation="1" result="blur" />
                      <feMerge>
                        <feMergeNode in="blur" />
                        <feMergeNode in="SourceGraphic" />
                      </feMerge>
                    </filter>
                  </defs>
                  {/* Flecha apuntando siempre hacia arriba */}
                  <path
                    d="M12 2L4 20l8-5 8 5L12 2z"
                    fill="url(#navGradient)"
                    stroke="white"
                    strokeWidth="2"
                    strokeLinejoin="round"
                    filter="url(#glow)"
                  />
                  <circle cx="12" cy="13" r="3" fill="white" />
                  <circle cx="12" cy="13" r="2" fill="#4285F4" />
                </svg>
              </div>
            ) : (
              <div className="relative w-6 h-6">
                <div className="absolute inset-0 bg-blue-500/50 rounded-full animate-ping-slow"></div>
                <div className="absolute inset-1.5 bg-blue-600 border-2 border-white rounded-full shadow-lg"></div>
              </div>
            )}
          </AdvancedMarker>
        )}
      </Map>

      <style>{`
        @keyframes ping-slow {
          0% { transform: scale(1); opacity: 1; }
          100% { transform: scale(2.5); opacity: 0; }
        }
        .animate-ping-slow {
          animation: ping-slow 2.5s cubic-bezier(0, 0, 0.2, 1) infinite;
        }
      `}</style>
    </div>
  );
};

export default MapView;
