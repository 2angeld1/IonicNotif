import React from 'react';
import { IonIcon } from '@ionic/react';
import { 
  closeCircleOutline,
  refreshOutline,
  volumeHighOutline,
  volumeMediumOutline,
  volumeMuteOutline
} from 'ionicons/icons';
import type { RouteStep, LatLng, VoiceMode } from '../types';
import { formatDistance } from '../utils/geoUtils';
import { useVoiceMode } from '../contexts/VoiceModeContext';

interface NavigationPanelProps {
  steps: RouteStep[];
  userLocation?: LatLng | null;
  onClose: () => void;
  onRecalculateRoute?: () => void;
  isOffRoute?: boolean;
}

const NavigationPanel: React.FC<NavigationPanelProps> = ({
  steps,
  onClose,
  onRecalculateRoute,
  isOffRoute = false
}) => {
  // Control de modo de voz
  const { voiceMode, cycleVoiceMode } = useVoiceMode();

  const getVoiceIcon = (mode: VoiceMode) => {
    switch (mode) {
      case 'all': return volumeHighOutline;
      case 'alerts': return volumeMediumOutline;
      case 'mute': return volumeMuteOutline;
    }
  };

  if (!steps || steps.length === 0) return null;

  // Calcular totales restantes
  const totalDistance = steps.reduce((acc, s) => acc + s.distance, 0);
  const totalDuration = steps.reduce((acc, s) => acc + s.duration, 0);

  // Simular tráfico (verde/amarillo/rojo) basado en duración
  // Lógica simple: si > 1 hora rojo, > 30 min amarillo (ejemplo muy básico, idealmente vendría del backend)
  const trafficColor = totalDuration > 3600 ? 'bg-red-500' : totalDuration > 1800 ? 'bg-amber-500' : 'bg-emerald-500';

  return (
    <div className="absolute bottom-4 left-4 right-4 z-[2000] flex flex-col items-center gap-2 animate-fade-in-up">
      {/* Alerta de Recálculo */}
      {isOffRoute && (
        <div onClick={onRecalculateRoute} className="bg-amber-500 text-white rounded-full px-4 py-1 flex items-center shadow-lg animate-pulse cursor-pointer">
          <IonIcon icon={refreshOutline} className="w-4 h-4 mr-2 animate-spin" />
          <span className="font-bold text-xs">Recalculando...</span>
        </div>
      )}

      <div className="w-full bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden flex items-center p-3 relative">
        {/* Barra de Tráfico Visual (Fondo sutil) */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-100 flex">
          <div className={`h-full w-full ${trafficColor} opacity-50`}></div>
        </div>

        {/* Info Principal */}
        <div className="flex-1 flex flex-col">
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-black text-gray-800 animate-pulse-slow">
              {Math.round(totalDuration / 60)} min
            </span>
            <span className="text-sm font-bold text-gray-500">
              ({formatDistance(totalDistance)})
            </span>
          </div>
          <span className="text-[10px] uppercase font-bold text-emerald-600 tracking-wider">
            Ruta más rápida
          </span>
        </div>

        {/* Controles Derecha */}
        <div className="flex items-center gap-3">
          {/* Control de Voz (Compacto) */}
          <button
            onClick={(e) => { e.stopPropagation(); cycleVoiceMode(); }}
            className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-gray-600 active:scale-95 transition-transform"
                >
            <IonIcon icon={getVoiceIcon(voiceMode)} className="text-xl" />
          </button>

          {/* Botón Salir (Destacado) */}
          <button
            onClick={onClose}
            className="w-10 h-10 bg-red-100 text-red-600 rounded-full flex items-center justify-center border border-red-200 shadow-sm active:scale-95 transition-transform"
          >
            <IonIcon icon={closeCircleOutline} className="text-2xl" />
          </button>
        </div>
      </div>

      <style>{`
        .animate-fade-in-up {
          animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}
      </style>
    </div>
  );
};

export default NavigationPanel;
