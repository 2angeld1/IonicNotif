import React from 'react';
import { IonIcon } from '@ionic/react';
import { 
  layersOutline, searchOutline, locationOutline, 
  carSportOutline, warningOutline, sparklesOutline 
} from 'ionicons/icons';

interface HomeFloatingButtonsProps {
  onOpenMapType: () => void;
  onOpenRouteModal: () => void;
  onOpenConvoyModal: () => void;
  onOpenIncidentModal: () => void;
  onRecenter: () => void;
  onOpenAIChat: () => void;
  hasUserLocation: boolean;
  isConvoyActive: boolean;
  apiAvailable: boolean;
}

const HomeFloatingButtons: React.FC<HomeFloatingButtonsProps> = ({
  onOpenMapType,
  onOpenRouteModal,
  onOpenConvoyModal,
  onOpenIncidentModal,
  onRecenter,
  onOpenAIChat,
  hasUserLocation,
  isConvoyActive,
  apiAvailable
}) => {
  return (
    <div className="absolute bottom-24 left-4 z-[1000] flex flex-col gap-3 items-center">
      
      {/* Botón IA (Nuevo) */}
      <button
        onClick={onOpenAIChat}
        className="w-14 h-14 bg-gradient-to-tr from-violet-600 to-indigo-600 shadow-xl text-white rounded-full flex items-center justify-center border-2 border-white/20 animate-pulse-slow"
        style={{ borderRadius: '50%' }}
      >
        <IonIcon icon={sparklesOutline} className="text-2xl" />
      </button>

      <button
        onClick={onOpenMapType}
        className="w-14 h-14 bg-white shadow-lg text-gray-700 rounded-full flex items-center justify-center border border-gray-200"
        style={{ borderRadius: '50%' }}
      >
        <IonIcon icon={layersOutline} className="text-2xl" />
      </button>

      <button
        onClick={onOpenRouteModal}
        className="w-14 h-14 bg-blue-600 shadow-lg text-white rounded-full flex items-center justify-center"
        style={{ borderRadius: '50%' }}
      >
        <IonIcon icon={searchOutline} className="text-2xl" />
      </button>

      {hasUserLocation && (
        <button
          onClick={onRecenter}
          className="w-14 h-14 bg-white shadow-lg text-blue-600 rounded-full flex items-center justify-center border border-gray-200"
          style={{ borderRadius: '50%' }}
        >
          <IonIcon icon={locationOutline} className="text-2xl" />
        </button>
      )}

      {/* Botón Convoy */}
      <button
        onClick={onOpenConvoyModal}
        className={`w-14 h-14 shadow-lg rounded-full flex items-center justify-center border border-gray-200 transition-all ${
          isConvoyActive ? 'bg-indigo-600 text-white animate-pulse' : 'bg-white text-indigo-600'
        }`}
        style={{ borderRadius: '50%' }}
      >
        <IonIcon icon={carSportOutline} className="text-2xl" />
      </button>

      {apiAvailable && (
        <button
          onClick={onOpenIncidentModal}
          className="w-14 h-14 bg-red-600 shadow-lg text-white rounded-full flex items-center justify-center"
          style={{ borderRadius: '50%' }}
        >
          <IonIcon icon={warningOutline} className="text-2xl" />
        </button>
      )}
    </div>
  );
};

export default HomeFloatingButtons;
