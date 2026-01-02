import React from 'react';
import { IonIcon } from '@ionic/react';
import {
  sunnyOutline,
  cloudOutline,
  rainyOutline,
  thunderstormOutline,
  snowOutline,
  waterOutline,
  thermometerOutline,
  eyeOutline,
} from 'ionicons/icons';
import type { WeatherInfo } from '../services/apiService';

interface WeatherBadgeProps {
  weather: WeatherInfo;
  compact?: boolean;
}

const WEATHER_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  clear: { icon: sunnyOutline, color: 'text-yellow-500', bg: 'bg-yellow-100' },
  clouds: { icon: cloudOutline, color: 'text-gray-500', bg: 'bg-gray-100' },
  rain: { icon: rainyOutline, color: 'text-blue-600', bg: 'bg-blue-100' },
  drizzle: { icon: rainyOutline, color: 'text-blue-400', bg: 'bg-blue-50' },
  thunderstorm: { icon: thunderstormOutline, color: 'text-purple-600', bg: 'bg-purple-100' },
  snow: { icon: snowOutline, color: 'text-blue-300', bg: 'bg-blue-50' },
  mist: { icon: waterOutline, color: 'text-gray-400', bg: 'bg-gray-100' },
  fog: { icon: waterOutline, color: 'text-gray-500', bg: 'bg-gray-200' },
};

const WeatherBadge: React.FC<WeatherBadgeProps> = ({ weather, compact = false }) => {
  const config = WEATHER_CONFIG[weather.condition] || WEATHER_CONFIG.clear;

  if (compact) {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full ${config.bg}`}>
        <IonIcon icon={config.icon} className={`w-4 h-4 ${config.color}`} />
        <span className="text-sm font-medium text-gray-700">
          {Math.round(weather.temperature)}°
        </span>
      </div>
    );
  }

  return (
    <div className={`rounded-xl p-3 ${config.bg}`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-xl bg-white/60 ${config.color}`}>
          <IonIcon icon={config.icon} className="w-8 h-8" />
        </div>
        
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-gray-800">
              {Math.round(weather.temperature)}°C
            </span>
            <span className="text-sm text-gray-600 capitalize">
              {weather.description}
            </span>
          </div>
          
          <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <IonIcon icon={thermometerOutline} className="w-3 h-3" />
              {weather.humidity}% humedad
            </span>
            <span className="flex items-center gap-1">
              <IonIcon icon={eyeOutline} className="w-3 h-3" />
              {(weather.visibility / 1000).toFixed(1)} km
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherBadge;
