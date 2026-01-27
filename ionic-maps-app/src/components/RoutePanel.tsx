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
  carOutline,
  gitBranchOutline,
  checkmarkCircle,
  sparkles,
  alertCircleOutline
} from 'ionicons/icons';
import type { RouteInfo, LatLng, FavoritePlace } from '../types';
import LocationSearch from './LocationSearch';
import { formatDistance, formatDuration } from '../utils/geoUtils';

interface RoutePanelProps {
  startLocation: { coords: LatLng | null; name: string };
  endLocation: { coords: LatLng | null; name: string };
  route: RouteInfo | null;
  alternativeRoutes?: RouteInfo[];
  selectedRouteIndex?: number;
  onSelectRoute?: (index: number) => void;
  isLoading: boolean;
  onStartChange: (coords: LatLng, name: string) => void;
  onEndChange: (coords: LatLng, name: string) => void;
  onCalculateRoute: () => void;
  onSwapLocations: () => void;
  onClear: () => void;
  onSaveTrip?: () => void;
  isSaving?: boolean;
  isRouteMode?: boolean;
  onToggleRouteMode?: () => void;
  modelStatus?: {
    trips_count: number;
    ready_for_training: boolean;
    is_trained: boolean;
  };
  favorites?: FavoritePlace[];
  userLocation?: LatLng | null;
  isModal?: boolean;
}

const RoutePanel: React.FC<RoutePanelProps> = ({
  startLocation,
  endLocation,
  route,
  alternativeRoutes = [],
  selectedRouteIndex = 0,
  onSelectRoute,
  isLoading,
  onStartChange,
  onEndChange,
  onCalculateRoute,
  onSwapLocations,
  onClear,
  onSaveTrip,
  isSaving = false,
  isRouteMode,
  onToggleRouteMode,
  modelStatus,
  favorites = [],
  userLocation,
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
                  userLocation={userLocation}
                />

                <LocationSearch
                  label=""
                  placeholder="🎯 Destino"
                  value={endLocation.name}
                  onLocationSelect={onEndChange}
                  color="red"
                  favorites={favorites}
                  userLocation={userLocation}
                />
              </div>

              {/* Botón swap */}
              <button
                onClick={onSwapLocations}
                className="self-center p-3.5 bg-gray-50 hover:bg-gray-100 border border-gray-100 rounded-2xl transition-all duration-200 hover:rotate-180 shadow-sm active:scale-95"
                title="Intercambiar ubicaciones"
              >
                <IonIcon icon={swapVerticalOutline} className="w-5 h-5 text-gray-700" />
              </button>
            </div>

            {/* Botones de acción principal */}
            <div className="flex gap-3 mt-4">
              <button
                onClick={onCalculateRoute}
                disabled={!startLocation.coords || !endLocation.coords || isLoading}
                className="group relative flex-1 overflow-hidden rounded-2xl bg-indigo-600 hover:bg-indigo-700 transition-colors duration-200 active:scale-95 shadow-lg shadow-indigo-200"
              >
                <div className="relative flex items-center justify-center gap-2 py-3.5 px-6 text-white font-bold">
                  {isLoading ? (
                    <IonSpinner name="crescent" className="w-5 h-5 text-white/80" />
                  ) : (
                    <>
                      <IonIcon icon={navigateOutline} className="w-5 h-5" />
                      <span className="text-sm tracking-wide">CALCULAR RUTA</span>
                    </>
                  )}
                </div>
              </button>

              <button
                onClick={onClear}
                className="flex items-center justify-center w-12 bg-white border border-gray-100 text-gray-400 hover:text-red-500 hover:border-red-100 hover:bg-red-50 rounded-2xl shadow-sm transition-all duration-200 active:scale-95"
                title="Limpiar"
              >
                <IonIcon icon={trashOutline} className="w-5 h-5" />
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

                {/* Selector de Rutas Alternativas */}
                {alternativeRoutes.length > 1 && onSelectRoute && (
                  <div className="mt-3 bg-white rounded-lg p-2 border border-gray-100">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <IonIcon icon={gitBranchOutline} className="w-4 h-4 text-indigo-600" />
                        <span className="text-[10px] font-bold text-gray-600 uppercase tracking-wide">
                          {alternativeRoutes.length} rutas disponibles
                        </span>
                      </div>
                      {alternativeRoutes.some(r => r.ml_recommended) && (
                        <div className="flex items-center gap-1 bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full text-[9px] font-bold">
                          <IonIcon icon={sparkles} className="w-3 h-3" />
                          Calitin ✨
                        </div>
                      )}
                    </div>
                    <div className="space-y-1.5 max-h-40 overflow-y-auto">
                      {alternativeRoutes.map((altRoute, index) => (
                        <button
                          key={index}
                          onClick={() => onSelectRoute(index)}
                          className={`w-full flex items-center justify-between p-2.5 rounded-lg transition-all duration-200 ${selectedRouteIndex === index
                            ? 'bg-indigo-100 border-2 border-indigo-400 shadow-sm'
                            : altRoute.ml_recommended
                              ? 'bg-purple-50 border border-purple-200 hover:bg-purple-100'
                              : 'bg-gray-50 border border-gray-200 hover:bg-gray-100'
                            }`}
                        >
                          <div className="flex items-center gap-2">
                            {selectedRouteIndex === index ? (
                              <IonIcon icon={checkmarkCircle} className="w-4 h-4 text-indigo-600" />
                            ) : altRoute.ml_recommended ? (
                              <IonIcon icon={sparkles} className="w-4 h-4 text-purple-500" />
                            ) : null}
                            <div className="text-left">
                              <div className="flex items-center gap-1.5">
                                <p className={`text-xs font-semibold ${selectedRouteIndex === index
                                  ? 'text-indigo-700'
                                  : altRoute.ml_recommended
                                    ? 'text-purple-700'
                                    : 'text-gray-700'
                                  }`}>
                                  {altRoute.summary || `Ruta ${index + 1}`}
                                </p>
                                {altRoute.ml_recommended && selectedRouteIndex !== index && (
                                  <span className="bg-purple-200 text-purple-700 text-[8px] px-1.5 py-0.5 rounded-full font-bold">
                                    🤖 Calitin
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-1.5 mt-0.5">
                                <span className="text-[10px] text-gray-500">
                                  {formatDistance(altRoute.distance)}
                                </span>
                                {altRoute.incidents_count && altRoute.incidents_count > 0 && (
                                  <span className="flex items-center gap-0.5 text-[9px] text-amber-600">
                                    <IonIcon icon={alertCircleOutline} className="w-3 h-3" />
                                    {altRoute.incidents_count} incid.
                                  </span>
                                )}
                                {altRoute.ml_confidence && altRoute.ml_confidence > 0 && (
                                  <span className="text-[9px] text-gray-400">
                                    • {Math.round(altRoute.ml_confidence * 100)}% conf.
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className={`text-right ${selectedRouteIndex === index
                            ? 'text-indigo-700'
                            : altRoute.ml_recommended
                              ? 'text-purple-700'
                              : 'text-gray-600'
                            }`}>
                            {/* Mostrar tiempo predicho si está disponible */}
                            {altRoute.predicted_duration && altRoute.predicted_duration !== altRoute.duration ? (
                              <>
                                <p className="text-xs font-bold">
                                  {formatDuration(altRoute.predicted_duration)}
                                </p>
                                <p className="text-[9px] text-gray-400 line-through">
                                  {formatDuration(altRoute.duration)}
                                </p>
                              </>
                            ) : (
                              <p className="text-xs font-bold">
                                {formatDuration(altRoute.duration_in_traffic || altRoute.duration)}
                              </p>
                            )}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                <div className="flex flex-col gap-3 mt-4">
                  {/* Botón Modo Ruta */}
                  {onToggleRouteMode && (
                    <button
                      onClick={onToggleRouteMode}
                      className={`relative w-full overflow-hidden rounded-2xl transition-all duration-200 active:scale-95 shadow-md ${isRouteMode
                        ? 'bg-orange-500 hover:bg-orange-600 shadow-orange-200'
                        : 'bg-blue-600 hover:bg-blue-700 shadow-blue-200'
                        }`}
                    >
                      <div className="relative flex items-center justify-center gap-3 py-3.5 px-4 text-white">
                        <IonIcon icon={carOutline} className="w-5 h-5" />
                        <span className="font-bold text-sm tracking-wide">
                          {isRouteMode ? 'DETENER NAVEGACIÓN' : 'INICIAR NAVEGACIÓN'}
                        </span>
                      </div>
                    </button>
                  )}

                  {/* Botón Guardar Viaje */}
                  {onSaveTrip && (
                    <button
                      onClick={onSaveTrip}
                      disabled={isSaving}
                      className={`group relative w-full overflow-hidden rounded-2xl transition-all duration-200 active:scale-95 shadow-md shadow-emerald-200 ${isSaving ? 'bg-emerald-400 cursor-not-allowed' : 'bg-emerald-600 hover:bg-emerald-700'}`}
                    >
                      <div className="relative flex items-center justify-center gap-2 py-3 px-4 text-white">
                        {isSaving ? (
                          <>
                            <IonSpinner name="crescent" className="w-4 h-4" />
                            <span className="font-semibold text-xs tracking-wider">GUARDANDO...</span>
                          </>
                        ) : (
                          <>
                              <IonIcon icon={saveOutline} className="w-4 h-4 opacity-90" />
                              <span className="font-semibold text-xs tracking-wider">ENSEÑAR A CALITIN 🤖</span>
                          </>
                        )}
                      </div>
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Panel de Estado ML */}
            {modelStatus && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="flex items-center justify-center gap-3 bg-gray-50 rounded-xl p-2.5">
                  <div className="text-[10px] text-gray-500 font-medium">
                    <span className="text-gray-900 font-bold text-sm">{modelStatus.trips_count}</span> viajes registrados
                  </div>
                  <div className="w-px h-4 bg-gray-300"></div>
                  <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide ${modelStatus.is_trained ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${modelStatus.is_trained ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`}></div>
                    {modelStatus.is_trained ? 'Calitin Listo 🤖' : 'Entrenando...'}
                  </div>
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
