import { useState, useEffect, useCallback } from 'react';
import { 
  checkApiHealth, 
  getIncidents, 
  getWeather, 
  getModelStatus, 
  getFavorites,
  addFavorite,
  confirmIncident,
  dismissIncident,
  createIncident,
  type Incident,
  type WeatherInfo,
  type IncidentType
} from '../services/apiService';
import type { LatLng, FavoritePlace, FavoriteType } from '../types';

export const useAppData = (defaultCenter: LatLng) => {
  const [apiAvailable, setApiAvailable] = useState(false);
  const [isBackendLoading, setIsBackendLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState('Despertando al servidor...');
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [weather, setWeather] = useState<WeatherInfo | null>(null);
  const [favorites, setFavorites] = useState<FavoritePlace[]>([]);
  const [modelStatus, setModelStatus] = useState({
    trips_count: 0,
    ready_for_training: false,
    is_trained: false
  });

  const refreshIncidents = useCallback(async (location: LatLng) => {
    const data = await getIncidents(location.lat, location.lng, 20);
    setIncidents(data);
  }, []);

  useEffect(() => {
    const initializeData = async () => {
      let isHealthy = false;
      let retries = 0;
      const maxRetries = 15;

      while (!isHealthy && retries < maxRetries) {
        if (retries > 0) setLoadingMessage(`Cargando sistema (${retries}/${maxRetries})...`);
        isHealthy = await checkApiHealth();
        if (!isHealthy) {
          await new Promise(resolve => setTimeout(resolve, 4000));
          retries++;
        }
      }

      setApiAvailable(isHealthy);
      setIsBackendLoading(false);
      
      if (isHealthy) {
        const [inc, wea, mod, fav] = await Promise.all([
          getIncidents(defaultCenter.lat, defaultCenter.lng, 20),
          getWeather(defaultCenter.lat, defaultCenter.lng),
          getModelStatus(),
          getFavorites()
        ]);
        setIncidents(inc);
        if (wea) setWeather(wea);
        setModelStatus(mod);
        setFavorites(fav);
      }
    };
    
    initializeData();
  }, [defaultCenter.lat, defaultCenter.lng]);

  const handleCreateFavorite = async (name: string, type: FavoriteType, location: LatLng) => {
    const newFav = await addFavorite({ name, location, type });
    if (newFav) setFavorites(prev => [...prev, newFav]);
    return newFav;
  };

  const handleConfirmIncident = async (incident: Incident) => {
    const id = incident.id || (incident as any)._id;
    if (id) {
      await confirmIncident(id);
      refreshIncidents(defaultCenter);
    }
  };

  const handleDismissIncident = async (incident: Incident) => {
    const id = incident.id || (incident as any)._id;
    if (id) {
      await dismissIncident(id);
      refreshIncidents(defaultCenter);
    }
  };

  const handleCreateIncident = async (location: LatLng, type: IncidentType, description?: string) => {
    const newInc = await createIncident(location, type, 'medium', description);
    if (newInc) {
      refreshIncidents(defaultCenter);
    }
    return newInc;
  };

  const handleSOS = useCallback(async (location: LatLng) => {
    // Feedback auditivo
    if ('speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance("Atención. Enviando señal de emergencia.");
      u.lang = 'es-ES';
      window.speechSynthesis.speak(u);
    }
    // SOS como prioridad alta
    const newInc = await createIncident(location, 'police', 'high', 'SOS: Emergencia reportada');
    if (newInc) refreshIncidents(location);
    return newInc;
  }, [refreshIncidents]);

  const clearIncidents = useCallback(() => setIncidents([]), []);

  return {
    apiAvailable,
    isBackendLoading,
    loadingMessage,
    incidents,
    weather,
    favorites,
    modelStatus,
    refreshIncidents,
    handleCreateFavorite,
    handleConfirmIncident,
    handleDismissIncident,
    handleCreateIncident,
    setModelStatus,
    clearIncidents,
    handleSOS
  };
};
