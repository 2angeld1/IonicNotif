import React from 'react';
import { IonIcon, IonSpinner } from '@ionic/react';
import {
  navigateOutline,
  timeOutline,
  speedometerOutline,
  swapVerticalOutline,
  trashOutline,
  flagOutline,
  saveOutline,
  carOutline
} from 'ionicons/icons';
import type { RouteInfo, LatLng, FavoritePlace } from '../types';
import LocationSearch from './LocationSearch';
import { formatDistance, formatDuration } from '../utils/geoUtils';

interface RoutePanelProps {
  startLocation: { coords: LatLng | null; name: string };
  endLocation: { coords: LatLng | null; name: string };
  route: RouteInfo | null;
  isLoading: boolean;
  onStartChange: (coords: LatLng, name: string) => void;
  onEndChange: (coords: LatLng, name: string) => void;
  onCalculateRoute: () => void;
  onSwapLocations: () => void;
  onClear: () => void;
  onSaveTrip?: () => void;
  isRouteMode?: boolean;
  onToggleRouteMode?: () => void;
  modelStatus?: {
    trips_count: number;
    ready_for_training: boolean;
    is_trained: boolean;
  };
  favorites?: FavoritePlace[];
  isModal?: boolean;
}

const RoutePanel: React.FC<RoutePanelProps> = ({
  startLocation,
  endLocation,
  route,
  isLoading,
  onStartChange,
  onEndChange,
  onCalculateRoute,
  onSwapLocations,
  onClear,
  onSaveTrip,
  isRouteMode,
  onToggleRouteMode,
  modelStatus,
  favorites = [],
  isModal = false,
}) => {


  return (
    <div className={isModal ? "w-full h-full" : "absolute top-0 left-0 right-0 z-[1000] p-2 flex justify-center"}>
      <div className={`${isModal ? "w-full" : "w-full max-w-sm bg-white/95 backdrop-blur-sm rounded-xl shadow-xl border border-gray-100 overflow-hidden"} transition-all duration-300`}>
        {/* Body */}
        <div className="h-full opacity-100">
          <div className={isModal ? "p-4" : "p-3"}>
            <div className="flex items-stretch gap-2">
              {/* Línea conectora */}
              <div className="flex flex-col items-center py-2">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-white shadow-md"></div>
                <div className="flex-1 w-0.5 bg-gradient-to-b from-emerald-500 to-rose-500 my-0.5"></div>
                <div className="w-2.5 h-2.5 rounded-full bg-rose-500 border-2 border-white shadow-md"></div>
              </div>

              {/* Inputs */}
              <div className="flex-1 space-y-3">
                <LocationSearch
                  label=""
                  placeholder="📍 Origen"
                  value={startLocation.name}
                  onLocationSelect={onStartChange}
                  color="green"
                  favorites={favorites}
                />

                <LocationSearch
                  label=""
                  placeholder="🎯 Destino"
                  value={endLocation.name}
                  onLocationSelect={onEndChange}
                  color="red"
                  favorites={favorites}
                />
              </div>

              {/* Botón swap */}
              <button
                onClick={onSwapLocations}
                className="self-center p-2 bg-gray-100 hover:bg-gray-200 rounded-xl transition-all duration-200 hover:rotate-180"
                title="Intercambiar ubicaciones"
              >
                <IonIcon icon={swapVerticalOutline} className="w-4 h-4 text-gray-600" />
              </button>
            </div>

            {/* Botones de acción */}
            <div className="flex gap-2 mt-3">
              <button
                onClick={onCalculateRoute}
                disabled={!startLocation.coords || !endLocation.coords || isLoading}
                className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-bold py-2.5 px-4 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl hover:-translate-y-0.5 disabled:shadow-none disabled:translate-y-0 text-xs uppercase tracking-wide"
              >
                {isLoading ? (
                  <IonSpinner name="crescent" className="w-4 h-4" />
                ) : (
                  <>
                    <IonIcon icon={navigateOutline} className="w-4 h-4" />
                    Calcular Ruta
                  </>
                )}
              </button>

              <button
                onClick={onClear}
                className="p-2 bg-gray-100 hover:bg-red-100 text-gray-600 hover:text-red-600 rounded-lg transition-all duration-200"
                title="Limpiar"
              >
                <IonIcon icon={trashOutline} className="w-4 h-4" />
              </button>
            </div>

            {/* Información de la ruta */}
            {route && (
              <div className="mt-3 bg-gradient-to-r from-emerald-50 to-blue-50 rounded-lg p-3 border border-emerald-100">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 bg-emerald-500 rounded-md flex items-center justify-center">
                    <IonIcon icon={flagOutline} className="w-3 h-3 text-white" />
                  </div>
                  <h3 className="font-bold text-gray-800 text-xs">
                    {route.isEstimate ? 'Ruta estimada' : 'Detalles de la Ruta'}
                  </h3>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-white rounded-md p-2 shadow-sm text-center">
                    <div className="flex items-center justify-center gap-1 text-blue-600 mb-0.5">
                      <IonIcon icon={speedometerOutline} className="w-3 h-3" />
                      <span className="text-[10px] font-medium uppercase tracking-wide">Distancia</span>
                    </div>
                    <p className="text-sm font-bold text-gray-800">
                      {formatDistance(route.distance)}
                    </p>
                  </div>

                  <div className="bg-white rounded-md p-2 shadow-sm text-center">
                    <div className="flex items-center justify-center gap-1 text-indigo-600 mb-0.5">
                      <IonIcon icon={timeOutline} className="w-3 h-3" />
                      <span className="text-[10px] font-medium uppercase tracking-wide">Tiempo</span>
                    </div>
                    <p className="text-sm font-bold text-gray-800">
                      {formatDuration(route.duration)}
                    </p>
                  </div>
                </div>

                <div className="flex flex-col gap-2 mt-3">
                  {/* Botón Modo Ruta */}
                  {onToggleRouteMode && (
                    <button
                      onClick={onToggleRouteMode}
                      className={`w-full ${isRouteMode ? 'bg-orange-500 hover:bg-orange-600' : 'bg-blue-600 hover:bg-blue-700'} text-white text-[10px] font-bold py-2 px-4 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 uppercase tracking-wide`}
                    >
                      <IonIcon icon={carOutline} className="w-4 h-4" />
                      {isRouteMode ? 'Salir Modo Ruta' : 'Iniciar Modo Ruta'}
                    </button>
                  )}

                  {/* Botón Guardar Viaje */}
                  {onSaveTrip && (
                    <button
                      onClick={onSaveTrip}
                      className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white text-[10px] font-bold py-2.5 px-4 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-sm hover:shadow-md uppercase tracking-wide"
                    >
                      <IonIcon icon={saveOutline} className="w-4 h-4" />
                      Guardar Viaje
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Panel de Estado ML */}
            {modelStatus && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="flex items-center justify-between bg-gray-50 rounded-lg p-2">
                  <div className="text-[10px] text-gray-600 w-full text-center">
                    <span className="font-bold text-gray-900">{modelStatus.trips_count}</span> viajes registrados
                  </div>
                  <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${modelStatus.is_trained ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                    {modelStatus.is_trained ? 'IA Lista' : 'Entrenando'}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoutePanel;
