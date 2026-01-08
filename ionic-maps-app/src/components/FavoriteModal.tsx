import React, { useState } from 'react';
import { 
  IonModal, 
  IonHeader, 
  IonToolbar, 
  IonTitle, 
  IonContent, 
  IonButton, 
  IonItem, 
  IonInput, 
  IonIcon
} from '@ionic/react';
import { homeOutline, briefcaseOutline, starOutline, locationOutline, closeOutline } from 'ionicons/icons';
import type { LatLng, FavoriteType } from '../types';

interface FavoriteModalProps {
  isOpen: boolean;
  location: LatLng | null;
  onClose: () => void;
  onFavoriteCreated: (name: string, type: FavoriteType) => void;
}

const FavoriteModal: React.FC<FavoriteModalProps> = ({
  isOpen,
  location,
  onClose,
  onFavoriteCreated,
}) => {
  const [name, setName] = useState('');
  const [type, setType] = useState<FavoriteType>('favorite');

  const handleSave = () => {
    if (name.trim()) {
      onFavoriteCreated(name, type);
      setName('');
      onClose();
    }
  };

  const handleTypeChange = (newType: FavoriteType) => {
    setType(newType);
    if (newType === 'home' && (!name || name === 'Trabajo')) setName('Casa');
    if (newType === 'work' && (!name || name === 'Casa')) setName('Trabajo');
  };

  return (
    <IonModal 
      isOpen={isOpen} 
      onDidDismiss={onClose} 
      initialBreakpoint={0.5} 
      breakpoints={[0, 0.5, 0.9]}
      className="favorite-modal"
    >
      <IonHeader className="ion-no-border">
        <IonToolbar>
          <IonTitle>Guardar Lugar</IonTitle>
          <IonButton slot="end" fill="clear" onClick={onClose} color="medium">
            <IonIcon icon={closeOutline} />
          </IonButton>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <div className="space-y-6">
          <div className="bg-blue-50 p-4 rounded-2xl flex items-center gap-3 border border-blue-100">
            <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center shadow-lg shadow-blue-200">
              <IonIcon icon={locationOutline} className="text-white w-6 h-6" />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wider text-blue-600 font-bold">Ubicación Seleccionada</p>
              <p className="text-xs text-gray-700 font-medium">
                {location ? `${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}` : 'No seleccionada'}
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-500 uppercase ml-1">¿Qué lugar es?</label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: 'home', label: 'Casa', icon: homeOutline, color: 'text-blue-500', bg: 'bg-blue-500' },
                { id: 'work', label: 'Trabajo', icon: briefcaseOutline, color: 'text-amber-500', bg: 'bg-amber-500' },
                { id: 'favorite', label: 'Favorito', icon: starOutline, color: 'text-pink-500', bg: 'bg-pink-500' },
                { id: 'other', label: 'Otro', icon: locationOutline, color: 'text-gray-500', bg: 'bg-gray-500' },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleTypeChange(item.id as FavoriteType)}
                  className={`flex items-center gap-3 p-3 rounded-2xl border-2 transition-all duration-200 ${
                    type === item.id 
                      ? 'border-blue-500 bg-white shadow-md scale-[1.02]' 
                      : 'border-transparent bg-gray-50'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${type === item.id ? item.bg : 'bg-white'} transition-colors`}>
                    <IonIcon 
                      icon={item.icon} 
                      className={`w-5 h-5 ${type === item.id ? 'text-white' : item.color}`} 
                    />
                  </div>
                  <span className={`text-sm font-bold ${type === item.id ? 'text-gray-900' : 'text-gray-500'}`}>
                    {item.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-500 uppercase ml-1">Nombre personalizado</label>
            <IonItem className="rounded-2xl overflow-hidden --background: #f3f4f6" lines="none">
              <IonInput 
                value={name} 
                onIonInput={(e) => setName(e.detail.value!)} 
                placeholder="Ej: Gimnasio, Escuela, Tienda..."
                className="font-bold"
              />
            </IonItem>
          </div>

          <button 
            onClick={handleSave} 
            disabled={!name.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-bold py-4 rounded-2xl transition-all active:scale-95 shadow-lg shadow-blue-200 mt-2"
          >
            Guardar en Favoritos
          </button>
        </div>
      </IonContent>
    </IonModal>
  );
};

export default FavoriteModal;
