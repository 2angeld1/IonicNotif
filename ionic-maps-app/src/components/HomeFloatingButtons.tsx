import React, { useState } from 'react';
import { IonIcon } from '@ionic/react';
import { 
  layersOutline, searchOutline, locationOutline, 
  carSportOutline, warningOutline, sparklesOutline, eyeOffOutline, addOutline,
  shareOutline, alertCircleOutline
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
  onClearIncidents?: () => void;
  onSOS?: () => void;
  onShareETA?: () => void;
  hasRoute?: boolean;
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
  apiAvailable,
  onClearIncidents,
  onSOS,
  onShareETA,
  hasRoute
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="absolute bottom-24 left-4 z-[1000] flex flex-col gap-4 items-center">
      
      {/* Botón IA (Siempre Visible) */}
      <button
        onClick={onOpenAIChat}
        className="w-14 h-14 bg-gradient-to-tr from-violet-600 to-indigo-600 shadow-xl text-white rounded-full flex items-center justify-center border-2 border-white/20 animate-pulse-slow"
        style={{ borderRadius: '50%' }}
      >
        <IonIcon icon={sparklesOutline} className="text-2xl" />
      </button>

      {/* Botón Recentrar (Siempre Visible si aplica) */}
      {hasUserLocation && (
        <button
          onClick={onRecenter}
          className="w-14 h-14 bg-white shadow-lg text-blue-600 rounded-full flex items-center justify-center border border-gray-200"
          style={{ borderRadius: '50%' }}
        >
          <IonIcon icon={locationOutline} className="text-2xl" />
        </button>
      )}

      {/* Menú Desplegable */}
      {isOpen && (
        <div className="flex flex-col gap-4 animate-fade-in-up items-center">

          {/* SOS Button (Top Priority) */}
          <button
            onClick={() => { onSOS?.(); setIsOpen(false); }}
            className="w-14 h-14 bg-red-700 shadow-xl text-white rounded-full flex items-center justify-center border-2 border-red-500 animate-pulse"
            style={{ borderRadius: '50%' }}
            title="SOS / Pánico"
          >
            <IonIcon icon={alertCircleOutline} className="text-3xl" />
          </button>

          {/* Share ETA (if routing) */}
          {hasRoute && (
            <button
              onClick={() => { onShareETA?.(); setIsOpen(false); }}
              className="w-14 h-14 bg-green-500 shadow-lg text-white rounded-full flex items-center justify-center"
              style={{ borderRadius: '50%' }}
              title="Compartir ETA"
            >
              <IonIcon icon={shareOutline} className="text-2xl" />
            </button>
          )}

          <button
            onClick={() => { onOpenRouteModal(); setIsOpen(false); }}
            className="w-14 h-14 bg-blue-600 shadow-lg text-white rounded-full flex items-center justify-center"
            style={{ borderRadius: '50%' }}
          >
            <IonIcon icon={searchOutline} className="text-2xl" />
          </button>

          <button
            onClick={() => { onOpenMapType(); setIsOpen(false); }}
            className="w-14 h-14 bg-white shadow-lg text-gray-700 rounded-full flex items-center justify-center border border-gray-200"
            style={{ borderRadius: '50%' }}
          >
            <IonIcon icon={layersOutline} className="text-2xl" />
          </button>

          <button
            onClick={() => { onOpenConvoyModal(); setIsOpen(false); }}
            className={`w-14 h-14 shadow-lg rounded-full flex items-center justify-center border border-gray-200 transition-all ${isConvoyActive ? 'bg-indigo-600 text-white animate-pulse' : 'bg-white text-indigo-600'
              }`}
            style={{ borderRadius: '50%' }}
          >
            <IonIcon icon={carSportOutline} className="text-2xl" />
          </button>

          {apiAvailable && (
            <>
              <button
                onClick={() => { onClearIncidents?.(); setIsOpen(false); }}
                className="w-14 h-14 bg-white shadow-lg text-gray-500 rounded-full flex items-center justify-center border border-gray-200"
                style={{ borderRadius: '50%' }}
                title="Ocultar incidentes"
              >
                <IonIcon icon={eyeOffOutline} className="text-2xl" />
              </button>

              <button
                onClick={() => { onOpenIncidentModal(); setIsOpen(false); }}
                className="w-14 h-14 bg-red-600 shadow-lg text-white rounded-full flex items-center justify-center"
                style={{ borderRadius: '50%' }}
              >
                <IonIcon icon={warningOutline} className="text-2xl" />
              </button>
            </>
          )}
        </div>
      )}

      {/* Botón Trigger del Menú */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-14 h-14 bg-gray-800 shadow-xl text-white rounded-full flex items-center justify-center transition-transform duration-300 ${isOpen ? 'rotate-45 bg-gray-700' : 'bg-gray-800'}`}
        style={{ borderRadius: '50%' }}
      >
        <IonIcon icon={addOutline} className="text-3xl" />
      </button>

    </div>
  );
};

export default HomeFloatingButtons;
