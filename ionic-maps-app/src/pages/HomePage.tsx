import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { IonPage, IonContent, IonToast, IonIcon, IonModal, IonActionSheet } from '@ionic/react';
import { warningOutline, locationOutline, searchOutline, navigateOutline } from 'ionicons/icons';

// Components
import MapView from '../components/MapView';
import RoutePanel from '../components/RoutePanel';
import IncidentModal from '../components/IncidentModal';
import WeatherBadge from '../components/WeatherBadge';
import IncidentCard from '../components/IncidentCard';
import NavigationPanel from '../components/NavigationPanel';
import FavoriteModal from '../components/FavoriteModal';

// Hooks
import { useUserLocation } from '../hooks/useUserLocation';
import { useAppData } from '../hooks/useAppData';
import { useNavigation } from '../hooks/useNavigation';

// Services & Utils
import { saveTrip, trainModel, getModelStatus, type TripData } from '../services/apiService';
import { formatDistance, formatDuration } from '../utils/geoUtils';
import type { LatLng } from '../types';
import type { Incident } from '../services/apiService';

const HomePage: React.FC = () => {
  // Configuración base
  const defaultCenter = useMemo(() => ({ lat: 8.9824, lng: -79.5199 }), []);

  // UI State
  const [toast, setToast] = useState({ show: false, message: '' });
  const [isIncidentModalOpen, setIsIncidentModalOpen] = useState(false);
  const [isFavoriteModalOpen, setIsFavoriteModalOpen] = useState(false);
  const [isRouteModalOpen, setIsRouteModalOpen] = useState(false);
  const [incidentLocation, setIncidentLocation] = useState<LatLng | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [favoriteLocation, setFavoriteLocation] = useState<LatLng | null>(null);
  const [isMapActionSheetOpen, setIsMapActionSheetOpen] = useState(false);
  const [mapClickLocation, setMapClickLocation] = useState<LatLng | null>(null);

  // Business Logic Hooks
  const {
    apiAvailable, isBackendLoading, loadingMessage, incidents, weather,
    favorites, modelStatus, handleCreateFavorite, handleConfirmIncident,
    handleDismissIncident, setModelStatus, refreshIncidents
  } = useAppData(defaultCenter);

  // Navigation state primero para tener acceso a la ruta
  const [internalRouteMode, setInternalRouteMode] = useState(false);
  const [internalRoute, setInternalRoute] = useState<import('../types').RouteInfo | null>(null);

  // Ubicación con suavizado y heading basado en ruta
  const { userLocation, userHeading, handleRecenter } = useUserLocation(internalRouteMode, internalRoute);

  // Luego la navegación que usa la ubicación
  const navigation = useNavigation(userLocation, incidents);

  const {
    startLocation: sLoc, setStartLocation: setSLoc,
    endLocation: eLoc, setEndLocation: setELoc,
    route: currentRoute, setRoute: setCurrentRoute,
    isRouteMode: routeMode, setIsRouteMode: setRouteMode,
    isOffRoute: offRoute, isLoading: routeLoading,
    handleCalculateRoute: calcRoute, handleRecalculateRoute: recalcRoute
  } = navigation;

  // Sincronizar ruta y modo para el hook de ubicación
  useEffect(() => {
    setInternalRouteMode(routeMode);
    setInternalRoute(currentRoute);
  }, [routeMode, currentRoute]);

  // Handlers locales para UI
  const onCalculateRoute = async () => {
    const result = await calcRoute();
    if (result) {
      const dist = formatDistance(result.distance);
      const time = formatDuration(result.duration);
      setToast({ show: true, message: `Ruta: ${dist} | ${time}` });
    } else {
      setToast({ show: true, message: 'No se pudo calcular la ruta' });
    }
  };

  const handleSaveTripAction = async () => {
    if (!currentRoute || !sLoc.coords || !eLoc.coords) return;
    const now = new Date();
    const tripData: TripData = {
      start: sLoc.coords,
      end: eLoc.coords,
      start_name: sLoc.name,
      end_name: eLoc.name,
      distance: currentRoute.distance,
      estimated_duration: currentRoute.duration, // Base sin tráfico
      actual_duration: currentRoute.duration_in_traffic || currentRoute.duration, // Con tráfico
      weather_condition: weather?.condition || 'unknown',
      temperature: weather?.temperature || 25,
      hour: now.getHours(),
      day_of_week: now.getDay(),
      traffic_intensity: currentRoute.duration_in_traffic ? currentRoute.duration_in_traffic / currentRoute.duration : 1.0,
    };

    const success = await saveTrip(tripData);
    if (success) {
      setToast({ show: true, message: 'Viaje guardado. Entrenando IA...' });
      await trainModel();
      const status = await getModelStatus();
      setModelStatus(status);
    }
  };

  const onMapClick = useCallback((location: LatLng) => {
    if (!apiAvailable) return;
    setMapClickLocation(location);
    setIsMapActionSheetOpen(true);
  }, [apiAvailable]);

  const handleMapActionSelect = (action: 'favorite' | 'incident') => {
    if (!mapClickLocation) return;
    if (action === 'favorite') {
      setFavoriteLocation(mapClickLocation);
      setIsFavoriteModalOpen(true);
    } else {
      setIncidentLocation(mapClickLocation);
      setIsIncidentModalOpen(true);
    }
    setIsMapActionSheetOpen(false);
    setMapClickLocation(null);
  };

  return (
    <IonPage>
      <IonContent className="ion-no-padding" fullscreen>
        <div className="relative w-full h-full">

          {/* Navegación Paso a Paso */}
          {routeMode && currentRoute?.steps && (
            <NavigationPanel
              steps={currentRoute.steps}
              userLocation={userLocation}
              isOffRoute={offRoute}
              onClose={() => setRouteMode(false)}
              onRecalculateRoute={recalcRoute}
            />
          )}

          {/* Modal Planificar Ruta */}
          <IonModal
            isOpen={isRouteModalOpen}
            onDidDismiss={() => setIsRouteModalOpen(false)}
            initialBreakpoint={0.65}
            breakpoints={[0, 0.4, 0.65, 0.95]}
          >
            <div className="h-full bg-white flex flex-col">
              <div className="p-4 flex items-center justify-between border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-50 rounded-xl text-blue-600"><IonIcon icon={navigateOutline} /></div>
                  <h2 className="text-gray-800 font-bold text-lg">Planificar Ruta</h2>
                </div>
                <button onClick={() => setIsRouteModalOpen(false)} className="p-2 opacity-50"><IonIcon icon={locationOutline} /></button>
              </div>

              <div className="flex-1 overflow-y-auto">
                <RoutePanel
                  startLocation={sLoc}
                  endLocation={eLoc}
                  route={currentRoute}
                  isLoading={routeLoading}
                  onStartChange={(c, n) => { setSLoc({ coords: c, name: n }); setCurrentRoute(null); }}
                  onEndChange={(c, n) => { setELoc({ coords: c, name: n }); setCurrentRoute(null); }}
                  onCalculateRoute={onCalculateRoute}
                  onSwapLocations={() => { const t = { ...sLoc }; setSLoc({ ...eLoc }); setELoc(t); setCurrentRoute(null); }}
                  onClear={() => { setSLoc({ coords: null, name: '' }); setELoc({ coords: null, name: '' }); setCurrentRoute(null); setRouteMode(false); }}
                  onSaveTrip={handleSaveTripAction}
                  modelStatus={modelStatus}
                  isRouteMode={routeMode}
                  onToggleRouteMode={() => { setRouteMode(!routeMode); if (!routeMode) setIsRouteModalOpen(false); }}
                  favorites={favorites}
                  isModal={true}
                />
              </div>
            </div>
          </IonModal>

          {/* Clima */}
          {weather && !routeMode && (
            <div className="absolute top-2 right-2 z-[1000]">
              <WeatherBadge weather={weather} compact />
            </div>
          )}

          {/* Mapa Principal */}
          <div className="w-full h-full">
            <MapView
              start={sLoc.coords}
              end={eLoc.coords}
              route={currentRoute}
              incidents={incidents}
              favorites={favorites}
              userLocation={userLocation}
              userHeading={userHeading}
              isRouteMode={routeMode}
              onMapClick={onMapClick}
              onIncidentClick={setSelectedIncident}
              onFavoriteClick={(fav) => { setELoc({ coords: fav.location, name: fav.name }); setIsRouteModalOpen(true); }}
            />
          </div>

          {/* Botones Flotantes */}
          {!routeMode && (
            <div className="absolute bottom-24 left-4 z-[1000] flex flex-col gap-3 items-center">
              <button
                onClick={() => setIsRouteModalOpen(true)}
                className="w-14 h-14 bg-blue-600 shadow-lg text-white rounded-full flex items-center justify-center"
                style={{ borderRadius: '50%' }}
              >
                <IonIcon icon={searchOutline} className="text-2xl" />
              </button>

              {userLocation && (
                <button
                  onClick={handleRecenter}
                  className="w-14 h-14 bg-white shadow-lg text-blue-600 rounded-full flex items-center justify-center border border-gray-200"
                  style={{ borderRadius: '50%' }}
                >
                  <IonIcon icon={locationOutline} className="text-2xl" />
                </button>
              )}

              {apiAvailable && (
                <button
                  onClick={() => { setIncidentLocation(sLoc.coords || defaultCenter); setIsIncidentModalOpen(true); }}
                  className="w-14 h-14 bg-red-600 shadow-lg text-white rounded-full flex items-center justify-center"
                  style={{ borderRadius: '50%' }}
                >
                  <IonIcon icon={warningOutline} className="text-2xl" />
                </button>
              )}
            </div>
          )}

          {/* Overlay de Carga */}
          {isBackendLoading && (
            <div className="fixed inset-0 z-[10000] flex flex-col items-center justify-center bg-white/80 backdrop-blur-xl text-center">
              <div className="w-24 h-24 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <h2 className="mt-8 text-2xl font-bold text-gray-800">Ionic Notif</h2>
              <p className="mt-2 text-gray-500 font-medium">{loadingMessage}</p>
            </div>
          )}

          {/* Modales Adicionales */}
          {selectedIncident && (
            <div className="absolute bottom-24 right-2 z-[1000] max-w-[280px]">
              <IncidentCard
                incident={selectedIncident}
                onConfirm={() => { handleConfirmIncident(selectedIncident); setSelectedIncident(null); }}
                onDismiss={() => { handleDismissIncident(selectedIncident); setSelectedIncident(null); }}
              />
              <button onClick={() => setSelectedIncident(null)} className="mt-2 w-full text-center text-sm text-gray-500">Cerrar</button>
            </div>
          )}

          <FavoriteModal
            isOpen={isFavoriteModalOpen}
            location={favoriteLocation}
            onClose={() => setIsFavoriteModalOpen(false)}
            onFavoriteCreated={async (n, t) => {
              if (favoriteLocation) {
                const fav = await handleCreateFavorite(n, t, favoriteLocation);
                if (fav) setToast({ show: true, message: `⭐ ${n} guardado` });
              }
            }}
          />

          <IncidentModal
            isOpen={isIncidentModalOpen}
            location={incidentLocation}
            onClose={() => setIsIncidentModalOpen(false)}
            onIncidentCreated={() => { setToast({ show: true, message: '⚠️ Reporte enviado' }); refreshIncidents(sLoc.coords || defaultCenter); }}
          />

          <IonToast
            isOpen={toast.show}
            message={toast.message}
            duration={2000}
            onDidDismiss={() => setToast({ show: false, message: '' })}
            position="bottom"
          />

          <IonActionSheet
            isOpen={isMapActionSheetOpen}
            onDidDismiss={() => { setIsMapActionSheetOpen(false); setMapClickLocation(null); }}
            header="¿Qué deseas agregar?"
            buttons={[
              {
                text: '⭐ Lugar Frecuente',
                handler: () => handleMapActionSelect('favorite')
              },
              {
                text: '⚠️ Reportar Incidencia',
                handler: () => handleMapActionSelect('incident')
              },
              {
                text: 'Cancelar',
                role: 'cancel'
              }
            ]}
          />
        </div>
      </IonContent>
    </IonPage>
  );
};

export default HomePage;
