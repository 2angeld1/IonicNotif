import React, { useState, useEffect } from 'react';
import { IonIcon } from '@ionic/react';
import { 
  arrowRedoOutline, 
  locationOutline, 
  chevronForwardOutline, 
  chevronBackOutline,
  closeCircleOutline
} from 'ionicons/icons';
import type { RouteStep } from '../types';

interface NavigationPanelProps {
  steps: RouteStep[];
  onClose: () => void;
}

const NavigationPanel: React.FC<NavigationPanelProps> = ({ steps, onClose }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  // Sintetizar un sonido de notificación premium
  const playNotificationSound = () => {
    const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();

    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // Nota La5
    oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.5);

    gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);

    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    oscillator.start();
    oscillator.stop(audioCtx.currentTime + 0.5);
  };

  useEffect(() => {
    if (currentStepIndex > 0) {
      playNotificationSound();
    }
  }, [currentStepIndex]);

  const currentStep = steps[currentStepIndex];

  if (!currentStep) return null;

  const formatDistance = (meters: number): string => {
    if (meters >= 1000) return `${(meters / 1000).toFixed(1)} km`;
    return `${Math.round(meters)} m`;
  };

  return (
    <div className="absolute top-4 left-0 right-0 z-[2000] px-4 animate-fade-in-down">
      <div className="bg-blue-600/95 backdrop-blur-md rounded-2xl shadow-2xl border border-blue-400 overflow-hidden text-white">
        <div className="p-4 flex items-center gap-4">
          {/* Icono de Maniobra */}
          <div className="bg-white/20 p-3 rounded-xl">
            <IonIcon icon={arrowRedoOutline} className="w-8 h-8 text-white" />
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
              <span>{formatDistance(currentStep.distance)}</span>
              {currentStep.name && (
                <>
                  <span className="opacity-50">•</span>
                  <span className="truncate max-w-[150px]">{currentStep.name}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Controles de Navegación */}
        <div className="bg-blue-700/50 flex border-t border-blue-400/30">
          <button
            disabled={currentStepIndex === 0}
            onClick={() => setCurrentStepIndex(prev => prev - 1)}
            className="flex-1 p-3 flex items-center justify-center gap-2 hover:bg-white/10 disabled:opacity-30 transition-all active:scale-95"
          >
            <IonIcon icon={chevronBackOutline} className="w-4 h-4" />
            <span className="text-sm font-bold">Anterior</span>
          </button>
          
          <div className="w-[1px] bg-blue-400/30" />
          
          <button
            disabled={currentStepIndex === steps.length - 1}
            onClick={() => setCurrentStepIndex(prev => prev + 1)}
            className="flex-1 p-3 flex items-center justify-center gap-2 hover:bg-white/10 disabled:opacity-30 transition-all active:scale-95 text-blue-50"
          >
            <span className="text-sm font-bold">Siguiente</span>
            <IonIcon icon={chevronForwardOutline} className="w-4 h-4" />
          </button>
        </div>
        
        {/* Barra de progreso visual */}
        <div className="h-1 bg-white/20 w-full">
          <div 
            className="h-full bg-emerald-400 transition-all duration-300" 
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
