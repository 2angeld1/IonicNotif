import React from 'react';
import { IonActionSheet } from '@ionic/react';
import { 
  mapOutline, earthOutline, globeOutline, imagesOutline 
} from 'ionicons/icons';

interface HomeActionSheetsProps {
  isMapActionSheetOpen: boolean;
  onDismissMapActionSheet: () => void;
  onMapActionSelect: (action: 'favorite' | 'incident') => void;
  
  isMapTypeActionSheetOpen: boolean;
  onDismissMapTypeActionSheet: () => void;
  onMapTypeSelect: (type: string) => void;
}

const HomeActionSheets: React.FC<HomeActionSheetsProps> = ({
  isMapActionSheetOpen,
  onDismissMapActionSheet,
  onMapActionSelect,
  isMapTypeActionSheetOpen,
  onDismissMapTypeActionSheet,
  onMapTypeSelect
}) => {
  return (
    <>
      <IonActionSheet
        isOpen={isMapActionSheetOpen}
        onDidDismiss={onDismissMapActionSheet}
        header="¿Qué deseas agregar?"
        buttons={[
          {
            text: '⭐ Lugar Frecuente',
            handler: () => onMapActionSelect('favorite')
          },
          {
            text: '⚠️ Reportar Incidencia',
            handler: () => onMapActionSelect('incident')
          },
          {
            text: 'Cancelar',
            role: 'cancel'
          }
        ]}
      />

      <IonActionSheet
        isOpen={isMapTypeActionSheetOpen}
        onDidDismiss={onDismissMapTypeActionSheet}
        header="Tipo de Mapa"
        buttons={[
          {
            text: 'Normal',
            icon: mapOutline,
            handler: () => onMapTypeSelect('roadmap')
          },
          {
            text: 'Satélite',
            icon: earthOutline,
            handler: () => onMapTypeSelect('satellite')
          },
          {
            text: 'Relieve / Terreno',
            icon: globeOutline,
            handler: () => onMapTypeSelect('terrain')
          },
          {
            text: 'Híbrido',
            icon: imagesOutline,
            handler: () => onMapTypeSelect('hybrid')
          },
          {
            text: 'Cancelar',
            role: 'cancel'
          }
        ]}
      />
    </>
  );
};

export default HomeActionSheets;
