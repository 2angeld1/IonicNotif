import React from 'react';
import { IonIcon } from '@ionic/react';
import {
  carOutline,
  constructOutline,
  warningOutline,
  pawOutline,
  shieldOutline,
  waterOutline,
  closeCircleOutline,
  speedometerOutline,
  locationOutline,
  checkmarkCircleOutline,
  closeOutline,
} from 'ionicons/icons';
import type { Incident } from '../services/apiService';

interface IncidentCardProps {
  incident: Incident;
  onConfirm?: () => void;
  onDismiss?: () => void;
  compact?: boolean;
}

const INCIDENT_CONFIG: Record<string, { icon: string; color: string; bgColor: string }> = {
  accident: { icon: carOutline, color: 'text-red-600', bgColor: 'bg-red-100' },
  road_work: { icon: constructOutline, color: 'text-orange-600', bgColor: 'bg-orange-100' },
  hazard: { icon: warningOutline, color: 'text-yellow-600', bgColor: 'bg-yellow-100' },
  animal: { icon: pawOutline, color: 'text-green-600', bgColor: 'bg-green-100' },
  police: { icon: shieldOutline, color: 'text-blue-600', bgColor: 'bg-blue-100' },
  flood: { icon: waterOutline, color: 'text-cyan-600', bgColor: 'bg-cyan-100' },
  closed_road: { icon: closeCircleOutline, color: 'text-gray-600', bgColor: 'bg-gray-200' },
  slow_traffic: { icon: speedometerOutline, color: 'text-amber-600', bgColor: 'bg-amber-100' },
  other: { icon: locationOutline, color: 'text-purple-600', bgColor: 'bg-purple-100' },
};

const SEVERITY_COLORS = {
  low: 'bg-green-400',
  medium: 'bg-yellow-400',
  high: 'bg-orange-500',
  critical: 'bg-red-600',
};

const INCIDENT_LABELS: Record<string, string> = {
  accident: 'Accidente',
  road_work: 'Obras en vía',
  hazard: 'Peligro',
  animal: 'Animal en vía',
  police: 'Control policial',
  flood: 'Inundación',
  closed_road: 'Vía cerrada',
  slow_traffic: 'Tráfico lento',
  other: 'Otro',
};

const IncidentCard: React.FC<IncidentCardProps> = ({
  incident,
  onConfirm,
  onDismiss,
  compact = false,
}) => {
  const config = INCIDENT_CONFIG[incident.type] || INCIDENT_CONFIG.other;
  const label = INCIDENT_LABELS[incident.type] || 'Incidencia';
  
  const timeAgo = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Hace un momento';
    if (diffMins < 60) return `Hace ${diffMins} min`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `Hace ${diffHours}h`;
    return `Hace ${Math.floor(diffHours / 24)}d`;
  };

  if (compact) {
    return (
      <div className={`flex items-center gap-2 p-2 rounded-lg ${config.bgColor}`}>
        <div className={`p-1.5 rounded-full bg-white/80 ${config.color}`}>
          <IonIcon icon={config.icon} className="w-4 h-4" />
        </div>
        <span className="text-sm font-medium text-gray-800">{label}</span>
        <span className={`ml-auto w-2 h-2 rounded-full ${SEVERITY_COLORS[incident.severity]}`} />
      </div>
    );
  }

  return (
    <div className={`rounded-xl overflow-hidden shadow-md ${config.bgColor}`}>
      <div className="p-3">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-xl bg-white/80 ${config.color}`}>
            <IonIcon icon={config.icon} className="w-6 h-6" />
          </div>
          
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h4 className="font-semibold text-gray-800">{label}</h4>
              <span className={`px-2 py-0.5 rounded-full text-xs text-white ${SEVERITY_COLORS[incident.severity]}`}>
                {incident.severity}
              </span>
            </div>
            
            {incident.description && (
              <p className="text-sm text-gray-600 mt-1">{incident.description}</p>
            )}
            
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span>{timeAgo(incident.created_at)}</span>
              <span>•</span>
              <span>{incident.confirmations} confirmaciones</span>
            </div>
          </div>
        </div>
        
        {(onConfirm || onDismiss) && (
          <div className="flex gap-2 mt-3">
            {onConfirm && (
              <button
                onClick={onConfirm}
                className="flex-1 flex items-center justify-center gap-1 py-2 bg-white/60 hover:bg-white rounded-lg text-sm font-medium text-green-700 transition-colors"
              >
                <IonIcon icon={checkmarkCircleOutline} className="w-4 h-4" />
                Confirmar
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="flex-1 flex items-center justify-center gap-1 py-2 bg-white/60 hover:bg-white rounded-lg text-sm font-medium text-gray-600 transition-colors"
              >
                <IonIcon icon={closeOutline} className="w-4 h-4" />
                Ya no está
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default IncidentCard;
