import React, { useEffect, useRef, useMemo } from 'react';
import { Map, AdvancedMarker, useMap } from '@vis.gl/react-google-maps';
import type { LatLng, RouteInfo, FavoritePlace, ConvoyMember, LocationSuggestion } from '../types';
import type { Incident } from '../services/apiService';
import { useMapController } from '../hooks/useMapController';
import { incidentIconConfig, favoriteIconConfig, mapConfig } from '../utils/mapConfigs';
import { IonIcon } from '@ionic/react';
import { carSport, car, bus, bicycle, walk } from 'ionicons/icons';

const vehicleIcons: Record<string, string> = {
  'sport': carSport,
  'sedan': car,
  'bus': bus,
  'bike': bicycle,
  'walk': walk
};

// Sub-componente para la Polilínea (con soporte para click)
const Polyline = (props: {
  points: google.maps.LatLngLiteral[],
  options?: google.maps.PolylineOptions,
  onClick?: () => void
}) => {
  const map = useMap();
  const polylineRef = useRef<google.maps.Polyline | null>(null);

  useEffect(() => {
    if (!map) return;
    polylineRef.current = new google.maps.Polyline({
      ...props.options,
      path: props.points,
      map: map,
      clickable: !!props.onClick
    });

    // Agregar listener de click si existe
    if (props.onClick) {
      polylineRef.current.addListener('click', props.onClick);
    }

    return () => {
      if (polylineRef.current) {
        google.maps.event.clearInstanceListeners(polylineRef.current);
        polylineRef.current.setMap(null);
      }
    };
  }, [map, props.points, props.options, props.onClick]);

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
  useMapController(props.start, props.end, props.route, props.userLocation, props.isRouteMode, props.userHeading, props.recenterTrigger);
  return null;
};

interface MapViewProps {
  start: LatLng | null;
  end: LatLng | null;
  route: RouteInfo | null;
  alternativeRoutes?: RouteInfo[];
  selectedRouteIndex?: number;
  onRouteClick?: (index: number) => void;
  incidents?: Incident[];
  favorites?: FavoritePlace[];
  convoyMembers?: ConvoyMember[]; // New prop
  userLocation?: LatLng | null;
  userHeading?: number | null;
  recenterTrigger?: number;
  mapTypeId?: string;
  isRouteMode?: boolean;
  onMapClick?: (location: LatLng) => void;
  onIncidentClick?: (incident: Incident) => void;
  onFavoriteClick?: (favorite: FavoritePlace) => void;
  isConvoyActive?: boolean;
  searchResults?: LocationSuggestion[];
  onSearchResultClick?: (result: LocationSuggestion) => void;
  userAvatar?: { type: string; color: string };
}

const MapView: React.FC<MapViewProps> = ({
  start, end, route,
  alternativeRoutes = [], selectedRouteIndex = 0, onRouteClick,
  incidents = [], favorites = [], convoyMembers = [], searchResults = [],
  userLocation, userHeading, recenterTrigger, mapTypeId = 'roadmap',
  isRouteMode = false, // Default to false if not provided
  isConvoyActive,
  onMapClick, onIncidentClick, onFavoriteClick, onSearchResultClick,
  userAvatar
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
        mapTypeId={mapTypeId}
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
          userHeading={userHeading} recenterTrigger={recenterTrigger}
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

        {/* Rutas Alternativas (en gris, clickeables) */}
        {alternativeRoutes.length > 1 && alternativeRoutes.map((altRoute, routeIdx) => {
          // ... (omitted same as before)
          if (routeIdx === selectedRouteIndex) return null;
          const points = altRoute.coordinates.map(([lng, lat]) => ({ lat, lng }));
          if (points.length < 2) return null;
          const routeColor = altRoute.ml_recommended ? '#9333ea' : '#6b7280';
          return (
            <React.Fragment key={`alt-${routeIdx}`}>
              <Polyline points={points} options={{ strokeColor: '#000000', strokeOpacity: 0.1, strokeWeight: 10, zIndex: 1 }} onClick={onRouteClick ? () => onRouteClick(routeIdx) : undefined} />
              <Polyline points={points} options={{ strokeColor: routeColor, strokeOpacity: altRoute.ml_recommended ? 0.7 : 0.4, strokeWeight: 6, zIndex: 2 }} onClick={onRouteClick ? () => onRouteClick(routeIdx) : undefined} />
              {altRoute.ml_recommended && (
                <Polyline points={points} options={{ strokeColor: '#c084fc', strokeOpacity: 0.8, strokeWeight: 3, zIndex: 3, icons: [{ icon: { path: google.maps.SymbolPath.CIRCLE, scale: 3, fillColor: '#c084fc', fillOpacity: 1, strokeWeight: 0 }, offset: '0', repeat: '20px' }] }} onClick={onRouteClick ? () => onRouteClick(routeIdx) : undefined} />
              )}
            </React.Fragment>
          );
        })}

        {/* Polilíneas de Ruta Principal */}
        {route && route.steps && route.steps.length > 0 ? (
          route.steps.map((step, idx) => {
            if (!step.path || step.path.length < 2) return null;
            let borderColor = '#151b54';
            if (step.traffic_status === 'severe') borderColor = '#b91c1c';
            else if (step.traffic_status === 'heavy') borderColor = '#c2410c';
            else if (step.traffic_status === 'moderate') borderColor = '#ca8a04';

            return (
              <React.Fragment key={idx}>
                <Polyline points={step.path} options={{ strokeColor: '#000000', strokeOpacity: 0.15, strokeWeight: 12, zIndex: 10 }} />
                <Polyline points={step.path} options={{ strokeColor: borderColor, strokeOpacity: 1, strokeWeight: 10, zIndex: 11 }} />
                <Polyline points={step.path} options={{ strokeColor: '#448aff', strokeOpacity: 1, strokeWeight: 6, zIndex: 12 }} />
              </React.Fragment>
            );
          })
        ) : (
            routePositions.length > 1 && (
            <>
                <Polyline points={routePositions} options={{ strokeColor: '#000000', strokeOpacity: 0.15, strokeWeight: 12, zIndex: 10 }} />
                <Polyline points={routePositions} options={{ strokeColor: '#151b54', strokeOpacity: 1, strokeWeight: 10, zIndex: 11 }} />
                <Polyline points={routePositions} options={{ strokeColor: '#448aff', strokeOpacity: 1, strokeWeight: 6, zIndex: 12 }} />
              </>
            )
        )}

        {/* Incidencias */}
        {incidents.map((incident, idx) => {
          const config = incidentIconConfig[incident.type] || incidentIconConfig.other;
          return (
            <AdvancedMarker key={incident.id || idx} position={incident.location} onClick={() => onIncidentClick?.(incident)} zIndex={1000}>
              <div className="w-8 h-8 rounded-full border-[3px] border-white shadow-md flex items-center justify-center text-sm" style={{ backgroundColor: config.color }}>
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
              <div className="w-8 h-8 rounded-xl border-[3px] border-white shadow-md flex items-center justify-center text-sm" style={{ backgroundColor: config.color }}>
                {config.emoji}
              </div>
            </AdvancedMarker>
          );
        })}

        {/* Resultados de Búsqueda */}
        {searchResults.map((result, idx) => {
          // Solo renderizar si tiene coordenadas válidas (distintas de '0')
          const lat = parseFloat(result.lat);
          const lng = parseFloat(result.lon);
          if (!lat || !lng || (lat === 0 && lng === 0)) return null;

          return (
            <AdvancedMarker
              key={result.place_id || idx}
              position={{ lat, lng }}
              onClick={() => onSearchResultClick?.(result)}
            >
              <div className="flex flex-col items-center">
                <div className="bg-white px-2 py-1 rounded-lg shadow-md mb-1 border border-purple-100 max-w-[120px]">
                  <p className="text-[10px] font-bold text-purple-700 truncate text-center">{result.display_name.split(',')[0]}</p>
                </div>
                <div className="w-8 h-8 rounded-full border-[3px] border-white shadow-md flex items-center justify-center text-sm bg-purple-600 text-white animate-bounce">
                  📍
                </div>
              </div>
            </AdvancedMarker>
          );
        })}

        {/* MIEMBROS DEL CONVOY (NUEVO) */}
        {convoyMembers.map((member) => (
          member.location && (
            <AdvancedMarker key={member.user_id} position={member.location} zIndex={900}>
              <div className="flex flex-col items-center">
                <div className="bg-white px-2 py-0.5 rounded-full shadow-md mb-1 border border-blue-100">
                  <p className="text-[10px] font-bold text-gray-800 whitespace-nowrap">{member.name}</p>
                </div>
                <div className="w-8 h-8 bg-blue-500 rounded-full border-[3px] border-white shadow-lg flex items-center justify-center text-white text-xs font-bold">
                  {member.name.charAt(0).toUpperCase()}
                </div>
              </div>
            </AdvancedMarker>
          )
        ))}

        {/* Ubicación del Usuario */}
        {userLocation && (
          <AdvancedMarker position={userLocation} zIndex={1000}>
            {/* Contenedor rotatorio para avatar */}
            {userAvatar && vehicleIcons[userAvatar.type] ? (
              <div
                className="relative flex items-center justify-center"
                style={{
                  transform: `rotate(${userHeading || 0}deg)`,
                  transition: 'transform 0.5s ease-out'
                }}
              >
                {/* Sombra/Glow */}
                <div className="absolute inset-0 bg-white/30 blur-md rounded-full transform scale-75"></div>
                <div
                  className="w-12 h-12 flex items-center justify-center filter drop-shadow-lg"
                  style={{ color: userAvatar.color }}
                >
                  <IonIcon icon={vehicleIcons[userAvatar.type]} className="text-4xl" />
                </div>
              </div>
            ) : (

              isRouteMode ? (
                <div className="w-14 h-14 flex items-center justify-center" style={{ filter: 'drop-shadow(0 6px 12px rgba(0,0,0,0.5))', transform: `rotate(${userHeading || 0}deg)`, transition: 'transform 0.5s ease-out' }}>
                <svg viewBox="0 0 24 24" className="w-full h-full">
                  <defs>
                    <linearGradient id="navGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="#4285F4" />
                      <stop offset="100%" stopColor="#1a73e8" />
                    </linearGradient>
                    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                      <feGaussianBlur stdDeviation="1" result="blur" />
                      <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                    </filter>
                  </defs>
                  <path d="M12 2L4 20l8-5 8 5L12 2z" fill="url(#navGradient)" stroke="white" strokeWidth="2" strokeLinejoin="round" filter="url(#glow)" />
                  <circle cx="12" cy="13" r="3" fill="white" />
                  <circle cx="12" cy="13" r="2" fill="#4285F4" />
                </svg>
              </div>
            ) : isConvoyActive ? (
              // Marcador personalizado para Modo Convoy (Soy yo)
              <div className="flex flex-col items-center">
                <div className="bg-indigo-600 px-2 py-0.5 rounded-full shadow-md mb-1 border border-indigo-200">
                  <p className="text-[10px] font-bold text-white whitespace-nowrap">TÚ</p>
                </div>
                <div className="relative w-8 h-8">
                  <div className="absolute inset-0 bg-indigo-500/50 rounded-full animate-ping-slow"></div>
                  <div className="absolute inset-0 bg-indigo-500 rounded-full border-[3px] border-white shadow-lg flex items-center justify-center text-white text-xs font-bold z-10">
                    You
                  </div>
                </div>
              </div>
            ) : (
              <div className="relative w-6 h-6">
                <div className="absolute inset-0 bg-blue-500/50 rounded-full animate-ping-slow"></div>
                <div className="absolute inset-1.5 bg-blue-600 border-2 border-white rounded-full shadow-lg"></div>
              </div>
                )

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
