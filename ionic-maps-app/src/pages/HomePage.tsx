import React, { useState, useCallback, useEffect } from 'react';
import { IonPage, IonContent, IonToast, IonFab, IonFabButton, IonIcon } from '@ionic/react';
import { warningOutline, refreshOutline } from 'ionicons/icons';
import MapView from '../components/MapView';
import RoutePanel from '../components/RoutePanel';
import IncidentModal from '../components/IncidentModal';
import WeatherBadge from '../components/WeatherBadge';
import IncidentCard from '../components/IncidentCard';
import NavigationPanel from '../components/NavigationPanel';
import FavoriteModal from '../components/FavoriteModal';
import { getRoute } from '../services/geocodingService';
import { 
  getIncidents, 
  confirmIncident, 
  dismissIncident,
  getWeather,
  checkApiHealth,
  saveTrip,
  trainModel,
  getModelStatus,
  getFavorites,
  addFavorite,
  type Incident,
  type WeatherInfo,
  type TripData
} from '../services/apiService';
import type { LatLng, RouteInfo, FavoritePlace, FavoriteType } from '../types';

const HomePage: React.FC = () => {
  const [startLocation, setStartLocation] = useState<{
    coords: LatLng | null;
    name: string;
  }>({ coords: null, name: '' });

  const [endLocation, setEndLocation] = useState<{
    coords: LatLng | null;
    name: string;
  }>({ coords: null, name: '' });

  const [route, setRoute] = useState<RouteInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; message: string }>({
    show: false,
    message: '',
  });
  
  // Nuevos estados para incidencias y clima
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [weather, setWeather] = useState<WeatherInfo | null>(null);
  const [isIncidentModalOpen, setIsIncidentModalOpen] = useState(false);
  const [incidentLocation, setIncidentLocation] = useState<LatLng | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [apiAvailable, setApiAvailable] = useState(false);
  const [userLocation, setUserLocation] = useState<LatLng | null>(null);
  const [isBackendLoading, setIsBackendLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState('Despertando al servidor...');

  // Estado del modelo ML
  const [modelStatus, setModelStatus] = useState<{
    trips_count: number;
    ready_for_training: boolean;
    is_trained: boolean;
  }>({ trips_count: 0, ready_for_training: false, is_trained: false });

  const [favorites, setFavorites] = useState<FavoritePlace[]>([]);
  const [isFavoriteModalOpen, setIsFavoriteModalOpen] = useState(false);
  const [favoriteLocation, setFavoriteLocation] = useState<LatLng | null>(null);

  // Estados de UI
  const [isPanelExpanded, setIsPanelExpanded] = useState(true);
  const [isRouteMode, setIsRouteMode] = useState(false);

  // Ciudad de Panamá por defecto
  const defaultCenter: LatLng = { lat: 8.9824, lng: -79.5199 };

  // Verificar disponibilidad del API y cargar datos iniciales con reintentos para Render
  useEffect(() => {
    const initializeData = async () => {
      let isHealthy = false;
      let retries = 0;
      const maxRetries = 15; // Aproximadamente 45-60 segundos

      while (!isHealthy && retries < maxRetries) {
        if (retries > 0) {
          setLoadingMessage(`Cargando sistema (${retries}/${maxRetries})...`);
        }
        isHealthy = await checkApiHealth();
        if (!isHealthy) {
          await new Promise(resolve => setTimeout(resolve, 4000));
          retries++;
        }
      }

      setApiAvailable(isHealthy);
      setIsBackendLoading(false);
      
      if (isHealthy) {
        // Cargar incidencias
        const incidentsData = await getIncidents(defaultCenter.lat, defaultCenter.lng, 20);
        setIncidents(incidentsData);
        
        // Cargar clima
        const weatherData = await getWeather(defaultCenter.lat, defaultCenter.lng);
        if (weatherData) setWeather(weatherData);

        // Cargar estado del modelo
        const status = await getModelStatus();
        setModelStatus(status);

        // Cargar lugares favoritos
        const favoritesData = await getFavorites();
        setFavorites(favoritesData);
      } else {
        setToast({ show: true, message: 'El servidor tardó demasiado en responder. Intenta recargar.' });
      }
    };
    
    initializeData();
  }, []);

  // Rastreo de ubicación del usuario en tiempo real
  useEffect(() => {
    if (!navigator.geolocation) {
      setToast({ show: true, message: 'Geolocalización no soportada en este navegador' });
      return;
    }

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const coords = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        setUserLocation(coords);

        setUserLocation(coords);

        // Si es la primera vez y no hay ubicación de inicio, usar la actual
        setStartLocation(prev => {
          if (!prev.coords) {
            return { coords, name: 'Mi ubicación' };
          }
          return prev;
        });
      },
      (error) => {
        console.error('Error de ubicación:', error);
        // No mostrar error constante, tal vez solo log
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 5000,
      }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  // Recargar incidencias
  const refreshIncidents = useCallback(async () => {
    const center = startLocation.coords || defaultCenter;
    const incidentsData = await getIncidents(center.lat, center.lng, 20);
    setIncidents(incidentsData);
  }, [startLocation.coords]);

  // Guardar viaje (Simulación)
  const handleSaveTrip = async () => {
    if (!route || !startLocation.coords || !endLocation.coords) return;

    const tripData: TripData = {
      start: startLocation.coords,
      end: endLocation.coords,
      start_name: startLocation.name || undefined,
      end_name: endLocation.name || undefined,
      distance: route.distance,
      estimated_duration: route.duration,
      actual_duration: route.duration,
    };

    const success = await saveTrip(tripData);
    if (success) {
      setToast({ show: true, message: 'Viaje guardado. Entrenando modelo...' });
      
      // Entrenar modelo automáticamente
      const trainResult = await trainModel();
      
      if (trainResult.success) {
         setToast({ show: true, message: `Viaje guardado y modelo entrenado (MAE: ${trainResult.mae?.toFixed(2)}s)` });
      } else {
         setToast({ show: true, message: 'Viaje guardado, pero error al entrenar modelo' });
      }

      // Actualizar estado del modelo
      const status = await getModelStatus();
      setModelStatus(status);
    } else {
      setToast({ show: true, message: 'Error al guardar el viaje' });
    }
  };

  const handleStartChange = useCallback((coords: LatLng, name: string) => {
    setStartLocation({ coords, name });
    setRoute(null);
  }, []);

  const handleEndChange = useCallback((coords: LatLng, name: string) => {
    setEndLocation({ coords, name });
    setRoute(null);
  }, []);

  const formatDistance = (meters: number): string => {
    if (meters >= 1000) {
      return `${(meters / 1000).toFixed(1)} km`;
    }
    return `${Math.round(meters)} m`;
  };

  const formatDuration = (seconds: number): string => {
    if (seconds === 0) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}min`;
    }
    return `${minutes} min`;
  };

  const handleCalculateRoute = useCallback(async () => {
    if (!startLocation.coords || !endLocation.coords) {
      setToast({
        show: true,
        message: 'Por favor, selecciona origen y destino',
      });
      return;
    }

    setIsLoading(true);
    try {
      const routeResult = await getRoute(startLocation.coords, endLocation.coords);
      if (routeResult) {
        setRoute(routeResult);
        
        const dist = formatDistance(routeResult.distance);
        const time = formatDuration(routeResult.duration);
        const startName = startLocation.name.split(',')[0];
        const endName = endLocation.name.split(',')[0];

        if (routeResult.isEstimate) {
           setToast({
            show: true,
            message: `No encontramos rutas, trazamos una: ${startName} - ${endName} | ${dist}`,
          });
        } else {
          setToast({
            show: true,
            message: `${startName} - ${endName} | ${dist} | ${time}`,
          });
        }

        // Colapsar panel automáticamente al encontrar ruta
        setIsPanelExpanded(false);
      } else {
        setToast({
          show: true,
          message: 'No se pudo calcular la ruta',
        });
      }
    } catch (error) {
      setToast({
        show: true,
        message: 'Error al calcular la ruta',
      });
    } finally {
      setIsLoading(false);
    }
  }, [startLocation, endLocation]);

  const handleSwapLocations = useCallback(() => {
    const tempStart = { ...startLocation };
    setStartLocation({ ...endLocation });
    setEndLocation(tempStart);
    setRoute(null);
  }, [startLocation, endLocation]);

  const handleClear = useCallback(() => {
    setStartLocation({ coords: null, name: '' });
    setEndLocation({ coords: null, name: '' });
    setRoute(null);
    setIsRouteMode(false);
    setIsPanelExpanded(true);
  }, []);

  // Manejar click en el mapa para crear incidencia
  const handleMapClick = useCallback((location: LatLng) => {
    if (!apiAvailable) {
      setToast({ show: true, message: 'Backend no disponible' });
      return;
    }
    setFavoriteLocation(location);
    setIsFavoriteModalOpen(true);
  }, [apiAvailable]);

  // Manejar creación de favorito
  const handleFavoriteCreated = async (name: string, type: FavoriteType) => {
    if (!favoriteLocation) return;

    const newFav = await addFavorite({
      name,
      location: favoriteLocation,
      type
    });

    if (newFav) {
      setFavorites(prev => [...prev, newFav]);
      setToast({ show: true, message: `⭐ ${name} guardado en tus lugares` });
    } else {
      setToast({ show: true, message: 'Error al guardar lugar' });
    }
  };

  // Manejar click en favorito (en el mapa)
  const handleFavoriteClick = useCallback((fav: FavoritePlace) => {
    setEndLocation({ coords: fav.location, name: fav.name });
    setIsPanelExpanded(true);
    setToast({ show: true, message: `Destino: ${fav.name}` });
  }, []);

  // Manejar click en incidencia
  const handleIncidentClick = useCallback((incident: Incident) => {
    setSelectedIncident(incident);
  }, []);

  // Confirmar incidencia
  const handleConfirmIncident = useCallback(async () => {
    if (selectedIncident) {
      const id = selectedIncident.id || (selectedIncident as any)._id || '';
      if (!id) {
        setToast({ show: true, message: 'ID de incidencia no disponible' });
        return;
      }
      await confirmIncident(id);
      setToast({ show: true, message: '✅ Incidencia confirmada' });
      setSelectedIncident(null);
      refreshIncidents();
    }
  }, [selectedIncident, refreshIncidents]);

  // Descartar incidencia
  const handleDismissIncident = useCallback(async () => {
    if (selectedIncident) {
      const id = selectedIncident.id || (selectedIncident as any)._id || '';
      if (!id) {
        setToast({ show: true, message: 'ID de incidencia no disponible' });
        return;
      }
      await dismissIncident(id);
      setToast({ show: true, message: '🗑️ Incidencia marcada como resuelta' });
      setSelectedIncident(null);
      refreshIncidents();
    }
  }, [selectedIncident, refreshIncidents]);

  return (
    <IonPage>
      <IonContent className="ion-no-padding" fullscreen>
        <div className="relative w-full h-full">
          {/* Panel de Navegación Paso a Paso (Modo Ruta) */}
          {isRouteMode && route?.steps && route.steps.length > 0 && (
            <NavigationPanel
              steps={route.steps}
              onClose={() => setIsRouteMode(false)}
            />
          )}

          {/* Panel de búsqueda de rutas */}
          <RoutePanel
            startLocation={startLocation}
            endLocation={endLocation}
            route={route}
            isLoading={isLoading}
            onStartChange={handleStartChange}
            onEndChange={handleEndChange}
            onCalculateRoute={handleCalculateRoute}
            onSwapLocations={handleSwapLocations}
            onClear={handleClear}
            onSaveTrip={handleSaveTrip}
            modelStatus={modelStatus}
            isExpanded={isPanelExpanded}
            onToggleExpand={() => setIsPanelExpanded(!isPanelExpanded)}
            isRouteMode={isRouteMode}
            onToggleRouteMode={() => {
              setIsRouteMode(!isRouteMode);
              if (!isRouteMode) setIsPanelExpanded(false);
            }}
            favorites={favorites}
          />

          {/* Badge de clima (Ocultar en modo ruta) */}
          {weather && !isRouteMode && (
            <div className="absolute top-2 right-2 z-[1000]">
              <WeatherBadge weather={weather} compact />
            </div>
          )}

          {/* Indicador de incidencias en ruta (Ocultar en modo ruta) */}
          {incidents.length > 0 && !isRouteMode && (
            <div className="absolute bottom-24 left-2 z-[1000] max-w-[200px]">
              <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg p-2">
                <div className="text-xs font-semibold text-gray-600 mb-1 flex items-center gap-1">
                  <IonIcon icon={warningOutline} className="w-3 h-3" />
                  {incidents.length} incidencias activas
                </div>
                <button
                  onClick={refreshIncidents}
                  className="text-xs text-blue-600 flex items-center gap-1 hover:text-blue-800"
                >
                  <IonIcon icon={refreshOutline} className="w-3 h-3" />
                  Actualizar
                </button>
              </div>
            </div>
          )}

          {/* Card de incidencia seleccionada */}
          {selectedIncident && (
            <div className="absolute bottom-24 right-2 z-[1000] max-w-[280px]">
              <IncidentCard
                incident={selectedIncident}
                onConfirm={handleConfirmIncident}
                onDismiss={handleDismissIncident}
              />
              <button
                onClick={() => setSelectedIncident(null)}
                className="mt-2 w-full text-center text-sm text-gray-500 hover:text-gray-700"
              >
                Cerrar
              </button>
            </div>
          )}

          {/* Mapa */}
          <div className="w-full h-full">
            <MapView
              start={startLocation.coords}
              end={endLocation.coords}
              route={route}
              incidents={incidents}
              favorites={favorites}
              userLocation={userLocation}
              isRouteMode={isRouteMode}
              onMapClick={handleMapClick}
              onIncidentClick={handleIncidentClick}
              onFavoriteClick={handleFavoriteClick}
              onRecenterUser={() => {
                if (userLocation) {
                  // Opcional: Centrar el mapa manualmente si fuera necesario aquí
                  // MapView ya lo maneja internamente con el botón
                }
              }}
            />
          </div>

          {/* FAB para crear incidencia (Ocultar en modo ruta) */}
          {apiAvailable && !isRouteMode && (
            <IonFab slot="fixed" vertical="bottom" horizontal="end">
              <IonFabButton
                color="danger"
                onClick={() => {
                  const center = startLocation.coords || defaultCenter;
                  setIncidentLocation(center);
                  setIsIncidentModalOpen(true);
                }}
              >
                <IonIcon icon={warningOutline} />
              </IonFabButton>
            </IonFab>
          )}

        </div>

        {/* Modal de favoritos */}
        <FavoriteModal
          isOpen={isFavoriteModalOpen}
          location={favoriteLocation}
          onClose={() => {
            setIsFavoriteModalOpen(false);
            setFavoriteLocation(null);
          }}
          onFavoriteCreated={handleFavoriteCreated}
        />

        {/* Modal de incidencia */}
        <IncidentModal
          isOpen={isIncidentModalOpen}
          location={incidentLocation}
          onClose={() => {
            setIsIncidentModalOpen(false);
            setIncidentLocation(null);
          }}
          onIncidentCreated={() => {
            setToast({ show: true, message: '⚠️ Incidencia reportada' });
            refreshIncidents();
          }}
        />

        <IonToast
          isOpen={toast.show}
          message={toast.message}
          duration={2000}
          onDidDismiss={() => setToast({ show: false, message: '' })}
          position="bottom"
        />

        {/* Pantalla de carga inicial (Overlay) para Render Cold Start */}
        {isBackendLoading && (
          <div className="fixed inset-0 z-[10000] flex flex-col items-center justify-center bg-white/80 backdrop-blur-xl">
            <div className="relative">
              {/* Spinner animado personalizado */}
              <div className="w-24 h-24 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <IonIcon icon={refreshOutline} className="w-8 h-8 text-blue-600 animate-pulse" />
              </div>
            </div>
            <h2 className="mt-8 text-2xl font-bold text-gray-800">Ionic Notif</h2>
            <p className="mt-2 text-gray-500 font-medium animate-pulse">{loadingMessage}</p>
            <div className="mt-12 flex gap-2">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        )}
      </IonContent>
    </IonPage>
  );
};

export default HomePage;
