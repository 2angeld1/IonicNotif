import React, { useState } from 'react';
import { IonModal, IonHeader, IonContent, IonIcon, IonFooter } from '@ionic/react';
import { carSport, car, bus, bicycle, walk, closeOutline, checkmarkCircle } from 'ionicons/icons';

interface AvatarSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (avatar: { type: string; color: string }) => void;
  currentAvatar?: { type: string; color: string };
}

const vehicles = [
  { id: 'sport', icon: carSport, label: 'Deportivo' },
  { id: 'sedan', icon: car, label: 'Sedán' },
  { id: 'bus', icon: bus, label: 'Van/Bus' },
  { id: 'bike', icon: bicycle, label: 'Moto/Bici' },
  { id: 'walk', icon: walk, label: 'Peatón' }
];

const colors = [
  '#ef4444', // Red
  '#3b82f6', // Blue
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#8b5cf6', // Violet
  '#ec4899', // Pink
  '#000000', // Black
  '#ffffff'  // White
];

const AvatarSelectorModal: React.FC<AvatarSelectorModalProps> = ({ 
  isOpen, onClose, onSave, currentAvatar 
}) => {
  const [selectedType, setSelectedType] = useState(currentAvatar?.type || 'sedan');
  const [selectedColor, setSelectedColor] = useState(currentAvatar?.color || '#3b82f6');

  const handleSave = () => {
    onSave({ type: selectedType, color: selectedColor });
    onClose();
  };

  return (
    <IonModal isOpen={isOpen} onDidDismiss={onClose} initialBreakpoint={0.6} breakpoints={[0, 0.6]}>
      <IonHeader className="ion-no-border">
        <div className="flex items-center justify-between p-4 bg-white">
          <h2 className="text-xl font-bold text-gray-800">Personaliza tu Vehículo</h2>
          <button onClick={onClose} className="p-2 bg-gray-100 rounded-full">
            <IonIcon icon={closeOutline} />
          </button>
        </div>
      </IonHeader>
      <IonContent className="ion-padding">
        
        {/* Preview */}
        <div className="flex justify-center mb-8">
            <div className="relative w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center shadow-inner">
                {/* Simulated Heading Rotation */}
                <div className="transform rotate-0 transition-all duration-300">
                     <IonIcon 
                        icon={vehicles.find(v => v.id === selectedType)?.icon} 
                        style={{ color: selectedColor, fontSize: '64px' }} 
                     />
                </div>
            </div>
        </div>

        <div className="space-y-6">
            {/* Tipo de Vehículo */}
            <div>
                <h3 className="text-sm font-semibold text-gray-500 mb-3 uppercase tracking-wider">Vehículo</h3>
                <div className="grid grid-cols-5 gap-2">
                    {vehicles.map(v => (
                        <button 
                            key={v.id}
                            onClick={() => setSelectedType(v.id)}
                            className={`flex flex-col items-center justify-center p-2 rounded-xl transition-all ${selectedType === v.id ? 'bg-blue-50 ring-2 ring-blue-500' : 'bg-gray-50 hover:bg-gray-100'}`}
                        >
                            <IonIcon icon={v.icon} className={`text-2xl mb-1 ${selectedType === v.id ? 'text-blue-600' : 'text-gray-600'}`} />
                            <span className="text-[10px] font-medium text-gray-600 truncate w-full text-center">{v.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Color */}
            <div>
                <h3 className="text-sm font-semibold text-gray-500 mb-3 uppercase tracking-wider">Color</h3>
                <div className="flex flex-wrap gap-3 justify-center">
                    {colors.map(c => (
                        <button
                            key={c}
                            onClick={() => setSelectedColor(c)}
                            className={`w-10 h-10 rounded-full shadow-sm flex items-center justify-center transition-transform ${selectedColor === c ? 'scale-110 ring-2 ring-offset-2 ring-gray-400' : ''}`}
                            style={{ backgroundColor: c, border: c === '#ffffff' ? '1px solid #e5e7eb' : 'none' }}
                        >
                            {selectedColor === c && (
                                <IonIcon icon={checkmarkCircle} className={`text-xl ${c === '#ffffff' ? 'text-black' : 'text-white'}`} />
                            )}
                        </button>
                    ))}
                </div>
            </div>
        </div>
      </IonContent>
      <IonFooter className="ion-no-border p-4 bg-white">
          <button 
            onClick={handleSave}
            className="w-full py-4 bg-blue-600 text-white rounded-2xl font-bold text-lg shadow-lg hover:bg-blue-700 active:scale-95 transition-all"
          >
              Guardar Avatar
          </button>
      </IonFooter>
    </IonModal>
  );
};

export default AvatarSelectorModal;
