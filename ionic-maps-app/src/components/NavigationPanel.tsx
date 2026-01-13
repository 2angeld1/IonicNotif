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
    <div className="absolute top-4 left-0 right-0 z-[2000] px-4 animate-fade-in-down">
      {/* Alerta de fuera de ruta */}
      {isOffRoute && onRecalculateRoute && (
        <div className="bg-amber-500 text-white rounded-xl p-3 mb-2 flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-2">
            <IonIcon icon={refreshOutline} className="w-5 h-5" />
            <span className="font-bold text-sm">Te has salido de la ruta</span>
          </div>
          <button
            onClick={onRecalculateRoute}
            className="bg-white text-amber-600 px-3 py-1 rounded-lg font-bold text-sm hover:bg-amber-50 transition-colors"
          >
            Recalcular
          </button>
        </div>
      )}

      <div className="bg-gradient-to-r from-blue-600 to-blue-700 backdrop-blur-md rounded-2xl shadow-2xl border border-blue-400/50 overflow-hidden text-white">
        {/* Paso actual */}
        <div className="p-4 flex items-center gap-4">
          {/* Icono de Maniobra */}
          <div className="bg-white/20 p-3 rounded-xl">
            <IonIcon icon={getManeuverIcon(currentStep.instruction)} className="w-8 h-8 text-white" />
          </div>

          {/* Instrucción */}
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-bold uppercase tracking-widest text-blue-100">
                Paso {currentStepIndex + 1} de {steps.length}
              </span>
              <button 
                onClick={onClose}
                className="p-1 hover:bg-white/10 rounded-full transition-colors"
              >
                <IonIcon icon={closeCircleOutline} className="w-5 h-5" />
              </button>
            </div>
            <h2 className="text-xl font-bold leading-tight line-clamp-2">
              {currentStep.instruction}
            </h2>
            <div className="flex items-center gap-2 mt-2 text-blue-100 font-medium">
              <IonIcon icon={locationOutline} className="w-4 h-4" />
              {distanceToNextStep !== null ? (
                <span className="font-bold">{formatDistance(distanceToNextStep)}</span>
              ) : (
                  <span>{formatDistance(currentStep.distance)}</span>
              )}
              {currentStep.name && (
                <>
                  <span className="opacity-50">•</span>
                  <span className="truncate max-w-[150px]">{currentStep.name}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Vista previa del siguiente paso */}
        {nextStep && (
          <div className="bg-blue-800/50 px-4 py-2 flex items-center gap-3 border-t border-blue-400/30">
            <IonIcon icon={getManeuverIcon(nextStep.instruction)} className="w-5 h-5 text-blue-200" />
            <div className="flex-1">
              <span className="text-[10px] uppercase tracking-wide text-blue-300">Luego</span>
              <p className="text-sm text-blue-100 line-clamp-1">{nextStep.instruction}</p>
            </div>
            <span className="text-xs font-bold text-blue-200">{formatDistance(nextStep.distance)}</span>
          </div>
        )}

        {/* Controles de Navegación */}
        <div className="bg-blue-700/50 flex border-t border-blue-400/30">
          <button
            disabled={currentStepIndex === 0}
            onClick={goToPreviousStep}
            className="flex-1 p-3 flex items-center justify-center gap-2 hover:bg-white/10 disabled:opacity-30 transition-all active:scale-95"
          >
            <IonIcon icon={chevronBackOutline} className="w-4 h-4" />
            <span className="text-sm font-bold">Anterior</span>
          </button>
          
          <div className="w-[1px] bg-blue-400/30" />
          
          <button
            disabled={currentStepIndex === steps.length - 1}
            onClick={goToNextStep}
            className="flex-1 p-3 flex items-center justify-center gap-2 hover:bg-white/10 disabled:opacity-30 transition-all active:scale-95 text-blue-50"
          >
            <span className="text-sm font-bold">Siguiente</span>
            <IonIcon icon={chevronForwardOutline} className="w-4 h-4" />
          </button>
        </div>
        
        {/* Barra de progreso visual */}
        <div className="h-1.5 bg-white/20 w-full">
          <div 
            className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 transition-all duration-500" 
            style={{ width: `${((currentStepIndex + 1) / steps.length) * 100}%` }}
          />
        </div>
      </div>

      <style>{`
        .animate-fade-in-down {
          animation: fadeInDown 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes fadeInDown {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default NavigationPanel;
