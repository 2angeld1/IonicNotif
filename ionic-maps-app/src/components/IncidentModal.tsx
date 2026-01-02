import React, { useState, useEffect } from 'react';
import {
  IonModal,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonButtons,
  IonButton,
  IonIcon,
  IonSpinner,
  IonTextarea,
} from '@ionic/react';
import {
  closeOutline,
  carOutline,
  constructOutline,
  warningOutline,
  pawOutline,
  shieldOutline,
  waterOutline,
  closeCircleOutline,
  speedometerOutline,
  locationOutline,
  sendOutline,
} from 'ionicons/icons';
import type { LatLng } from '../types';
import type { IncidentType } from '../services/apiService';
import { createIncident } from '../services/apiService';

interface IncidentModalProps {
  isOpen: boolean;
  location: LatLng | null;
  onClose: () => void;
  onIncidentCreated: () => void;
}

const INCIDENT_TYPES: {
  value: IncidentType;
  label: string;
  icon: string;
  color: string;
}[] = [
  { value: 'accident', label: 'Accidente', icon: carOutline, color: 'bg-red-500' },
  { value: 'road_work', label: 'Obras', icon: constructOutline, color: 'bg-orange-500' },
  { value: 'hazard', label: 'Peligro', icon: warningOutline, color: 'bg-yellow-500' },
  { value: 'animal', label: 'Animal', icon: pawOutline, color: 'bg-green-500' },
  { value: 'police', label: 'Policía', icon: shieldOutline, color: 'bg-blue-500' },
  { value: 'flood', label: 'Inundación', icon: waterOutline, color: 'bg-cyan-500' },
  { value: 'closed_road', label: 'Vía cerrada', icon: closeCircleOutline, color: 'bg-gray-600' },
  { value: 'slow_traffic', label: 'Tráfico lento', icon: speedometerOutline, color: 'bg-amber-500' },
  { value: 'other', label: 'Otro', icon: locationOutline, color: 'bg-purple-500' },
];

const SEVERITIES = [
  { value: 'low', label: 'Bajo', color: 'bg-green-400' },
  { value: 'medium', label: 'Medio', color: 'bg-yellow-400' },
  { value: 'high', label: 'Alto', color: 'bg-orange-500' },
  { value: 'critical', label: 'Crítico', color: 'bg-red-600' },
] as const;

const IncidentModal: React.FC<IncidentModalProps> = ({
  isOpen,
  location,
  onClose,
  onIncidentCreated,
}) => {
  const [selectedType, setSelectedType] = useState<IncidentType | null>(null);
  const [severity, setSeverity] = useState<'low' | 'medium' | 'high' | 'critical'>('medium');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      // Reset form when closed
      setSelectedType(null);
      setSeverity('medium');
      setDescription('');
    }
  }, [isOpen]);

  const handleSubmit = async () => {
    if (!location || !selectedType) return;

    setIsSubmitting(true);
    try {
      const incident = await createIncident(
        location,
        selectedType,
        severity,
        description || undefined
      );

      if (incident) {
        onIncidentCreated();
        onClose();
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <IonModal isOpen={isOpen} onDidDismiss={onClose}>
      <IonHeader>
        <IonToolbar color="danger">
          <IonTitle>⚠️ Reportar incidencia</IonTitle>
          <IonButtons slot="end">
            <IonButton onClick={onClose}>
              <IonIcon icon={closeOutline} />
            </IonButton>
          </IonButtons>
        </IonToolbar>
      </IonHeader>

      <IonContent className="ion-padding">
        <div className="space-y-6">
          {/* Tipo de incidencia */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              ¿Qué tipo de incidencia es?
            </h3>
            <div className="grid grid-cols-3 gap-2">
              {INCIDENT_TYPES.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setSelectedType(type.value)}
                  className={`p-3 rounded-xl flex flex-col items-center gap-1 transition-all ${
                    selectedType === type.value
                      ? `${type.color} text-white shadow-lg scale-105`
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  <IonIcon icon={type.icon} className="w-6 h-6" />
                  <span className="text-xs font-medium">{type.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Severidad */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              Gravedad
            </h3>
            <div className="flex gap-2">
              {SEVERITIES.map((sev) => (
                <button
                  key={sev.value}
                  onClick={() => setSeverity(sev.value)}
                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    severity === sev.value
                      ? `${sev.color} text-white shadow-md`
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {sev.label}
                </button>
              ))}
            </div>
          </div>

          {/* Descripción opcional */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              Descripción (opcional)
            </h3>
            <IonTextarea
              value={description}
              onIonChange={(e) => setDescription(e.detail.value || '')}
              placeholder="Describe brevemente la situación..."
              rows={3}
              className="bg-gray-100 rounded-xl px-3"
            />
          </div>

          {/* Ubicación */}
          {location && (
            <div className="bg-blue-50 rounded-xl p-3 text-sm text-blue-700">
              📍 Ubicación: {location.lat.toFixed(6)}, {location.lng.toFixed(6)}
            </div>
          )}

          {/* Botón enviar */}
          <button
            onClick={handleSubmit}
            disabled={!selectedType || isSubmitting}
            className="w-full bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 disabled:from-gray-400 disabled:to-gray-400 text-white font-bold py-4 px-6 rounded-xl shadow-lg disabled:shadow-none transition-all flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <IonSpinner name="crescent" className="w-5 h-5" />
            ) : (
              <>
                <IonIcon icon={sendOutline} className="w-5 h-5" />
                Reportar incidencia
              </>
            )}
          </button>
        </div>
      </IonContent>
    </IonModal>
  );
};

export default IncidentModal;
