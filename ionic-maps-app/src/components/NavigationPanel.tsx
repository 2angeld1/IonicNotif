import React from 'react';
import { IonIcon } from '@ionic/react';
import { 
  locationOutline, 
  chevronForwardOutline, 
  chevronBackOutline,
  closeCircleOutline,
  refreshOutline
} from 'ionicons/icons';
import type { RouteStep, LatLng } from '../types';
import { formatDistance, getManeuverIcon } from '../utils/geoUtils';
import { useRouteStepProgress } from '../hooks/useRouteStepProgress';

interface NavigationPanelProps {
  steps: RouteStep[];
  userLocation?: LatLng | null;
  onClose: () => void;
  onRecalculateRoute?: () => void;
  isOffRoute?: boolean;
}

const NavigationPanel: React.FC<NavigationPanelProps> = ({
  steps,
  userLocation,
  onClose,
  onRecalculateRoute,
  isOffRoute = false
}) => {
  const {
    currentStepIndex,
    distanceToNextStep,
    goToNextStep,
    goToPreviousStep
  } = useRouteStepProgress(steps, userLocation);

  const currentStep = steps[currentStepIndex];
  const nextStep = steps[currentStepIndex + 1];

  if (!currentStep) return null;

  return (
    <div className="absolute bottom-0 left-0 right-0 z-[2000] px-2 pb-2 animate-fade-in-up">
      {/* Alerta de Recálculo Automático (Clickeable por si acaso) */}
      {isOffRoute && (
        <div
          onClick={onRecalculateRoute}
          className="bg-amber-500 text-white rounded-xl p-2 mb-1.5 flex items-center justify-center shadow-lg animate-pulse cursor-pointer active:scale-95 transition-transform"
        >
          <IonIcon icon={refreshOutline} className="w-4 h-4 mr-2 animate-spin" />
          <span className="font-bold text-xs">Recalculando ruta...</span>
        </div>
      )}

      <div className="bg-gradient-to-r from-blue-600 to-blue-700 backdrop-blur-md rounded-xl shadow-2xl border border-blue-400/50 overflow-hidden text-white">
        {/* Barra de progreso visual - En la parte superior */}
        <div className="h-1 bg-white/20 w-full">
          <div
            className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 transition-all duration-500"
            style={{ width: `${((currentStepIndex + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Paso actual - Compacto */}
        <div className="p-2.5 flex items-center gap-2.5">
          {/* Icono de Maniobra */}
          <div className="bg-white/20 p-2 rounded-lg shrink-0">
            <IonIcon icon={getManeuverIcon(currentStep.instruction)} className="w-6 h-6 text-white" />
          </div>

          {/* Instrucción */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-[9px] font-bold uppercase tracking-widest text-blue-100">
                Paso {currentStepIndex + 1}/{steps.length}
              </span>
              <button 
                onClick={onClose}
                className="p-0.5 hover:bg-white/10 rounded-full transition-colors"
              >
                <IonIcon icon={closeCircleOutline} className="w-4 h-4" />
              </button>
            </div>
            <h2 className="text-sm font-bold leading-tight line-clamp-1">
              {currentStep.instruction}
            </h2>
            <div className="flex items-center gap-1.5 mt-0.5 text-blue-100 text-xs">
              <IonIcon icon={locationOutline} className="w-3 h-3" />
              {distanceToNextStep !== null ? (
                <span className="font-bold">{formatDistance(distanceToNextStep)}</span>
              ) : (
                  <span>{formatDistance(currentStep.distance)}</span>
              )}
              {currentStep.name && (
                <>
                  <span className="opacity-50">•</span>
                  <span className="truncate max-w-[120px] text-[10px]">{currentStep.name}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Vista previa del siguiente paso - Muy compacta */}
        {nextStep && (
          <div className="bg-blue-800/50 px-2.5 py-1.5 flex items-center gap-2 border-t border-blue-400/30">
            <IonIcon icon={getManeuverIcon(nextStep.instruction)} className="w-4 h-4 text-blue-200 shrink-0" />
            <div className="flex-1 min-w-0">
              <span className="text-[9px] uppercase tracking-wide text-blue-300">Luego</span>
              <p className="text-xs text-blue-100 line-clamp-1">{nextStep.instruction}</p>
            </div>
            <span className="text-[10px] font-bold text-blue-200 shrink-0">{formatDistance(nextStep.distance)}</span>
          </div>
        )}

        {/* Controles de Navegación - Compactos */}
        <div className="bg-blue-700/50 flex border-t border-blue-400/30">
          <button
            disabled={currentStepIndex === 0}
            onClick={goToPreviousStep}
            className="flex-1 py-2 flex items-center justify-center gap-1.5 hover:bg-white/10 disabled:opacity-30 transition-all active:scale-95"
          >
            <IonIcon icon={chevronBackOutline} className="w-3.5 h-3.5" />
            <span className="text-xs font-bold">Anterior</span>
          </button>
          
          <div className="w-[1px] bg-blue-400/30" />
          
          <button
            disabled={currentStepIndex === steps.length - 1}
            onClick={goToNextStep}
            className="flex-1 py-2 flex items-center justify-center gap-1.5 hover:bg-white/10 disabled:opacity-30 transition-all active:scale-95 text-blue-50"
          >
            <span className="text-xs font-bold">Siguiente</span>
            <IonIcon icon={chevronForwardOutline} className="w-3.5 h-3.5" />
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
