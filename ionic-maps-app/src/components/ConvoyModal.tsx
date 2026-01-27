import React, { useState } from 'react';
import { 
  IonModal, IonHeader, IonToolbar, IonTitle, IonContent, 
  IonButton, IonIcon, IonLabel, IonSegment, IonSegmentButton
} from '@ionic/react';
import { closeOutline, carSportOutline, searchOutline, peopleOutline, copyOutline, exitOutline } from 'ionicons/icons';
import { useConvoy } from '../contexts/ConvoyContext';
import type { LatLng } from '../types';

interface ConvoyModalProps {
  isOpen: boolean;
  onClose: () => void;
  userLocation: LatLng | null;
}

const ConvoyModal: React.FC<ConvoyModalProps> = ({ isOpen, onClose, userLocation }) => {
  const { convoy, create, join, leave, userId } = useConvoy();
  const [mode, setMode] = useState<'create' | 'join'>('create');
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCreate = async () => {
    if (!name.trim() || !userLocation) return;
    setIsLoading(true);
    setError('');
    try {
      const success = await create(name, userLocation);
      if (!success) setError('Error creando convoy');
    } catch (e) {
      setError('Error de conexión');
    } finally {
      setIsLoading(false);
    }
  };

  const handleJoin = async () => {
    if (!name.trim() || !code.trim() || !userLocation) return;
    setIsLoading(true);
    setError('');
    try {
      const success = await join(code, name, userLocation);
      if (!success) setError('Código inválido o error de conexión');
    } catch (e) {
      setError('Error al unirse');
    } finally {
      setIsLoading(false);
    }
  };

  const copyCode = () => {
    if (convoy?.code) {
      navigator.clipboard.writeText(convoy.code);
      // Podríamos mostrar un toast aquí
    }
  };

  return (
    <IonModal isOpen={isOpen} onDidDismiss={onClose} initialBreakpoint={0.6} breakpoints={[0, 0.6, 0.9]} className="rounded-t-2xl">
      <IonHeader className="ion-no-border">
        <IonToolbar>
          <IonTitle>Modo Convoy 🚗</IonTitle>
          <IonButton slot="end" fill="clear" onClick={onClose} color="medium">
            <IonIcon icon={closeOutline} />
          </IonButton>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        
        {/* VISTA ACTIVA: Ya estás en un convoy */}
        {convoy ? (
          <div className="flex flex-col h-full gap-4">
            <div className="bg-blue-600 rounded-3xl p-6 text-white shadow-lg relative overflow-hidden">
               <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl -mr-10 -mt-10"></div>
               
               <p className="text-sm opacity-80 font-medium mb-1">CÓDIGO DE GRUPO</p>
               <div className="flex items-center gap-3">
                 <h1 className="text-5xl font-black tracking-widest">{convoy.code}</h1>
                 <button onClick={copyCode} className="bg-white/20 p-2 rounded-full hover:bg-white/30 transition-colors">
                    <IonIcon icon={copyOutline} />
                 </button>
               </div>
               <p className="text-xs mt-2 opacity-70">Comparte este código con tus amigos para que aparezcan en tu mapa.</p>
            </div>

            <div className="flex-1 overflow-y-auto">
                <h3 className="font-bold text-gray-800 ml-1 mb-2 flex items-center gap-2">
                    <IonIcon icon={peopleOutline} className="text-blue-600"/>
                    Miembros ({convoy.members.length})
                </h3>
                <div className="space-y-2">
                    {convoy.members.map(member => (
                        <div key={member.user_id} className="bg-gray-50 p-3 rounded-2xl flex items-center gap-3 border border-gray-100">
                             <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold shadow-sm ${member.user_id === userId ? 'bg-blue-100 text-blue-600' : 'bg-white text-gray-600 border border-gray-200'}`}>
                                {member.name.charAt(0).toUpperCase()}
                             </div>
                             <div className="flex-1">
                                <p className="font-bold text-gray-800 flex items-center gap-2">
                                    {member.name}
                                    {member.user_id === convoy.host_id && <span className="text-[10px] bg-yellow-100 text-yellow-800 px-1.5 rounded-full">HOST</span>}
                                    {member.user_id === userId && <span className="text-[10px] bg-blue-100 text-blue-800 px-1.5 rounded-full">TÚ</span>}
                                </p>
                                <p className="text-xs text-gray-500">
                                    {member.status === 'online' ? '🟢 En línea' : '⚪ Desconectado'} 
                                    {/* Podríamos poner distancia aquí si tuviéramos cálculo */}
                                </p>
                             </div>
                        </div>
                    ))}
                </div>
            </div>

            <button 
              onClick={leave}
              className="w-full bg-red-50 text-red-600 font-bold py-4 rounded-2xl flex items-center justify-center gap-2 hover:bg-red-100 transition-colors"
            >
                <IonIcon icon={exitOutline} />
                Salir del Convoy
            </button>
          </div>
        ) : (
        // VISTA INICIAL: Crear o Unirse
          <div className="space-y-6">
             <IonSegment value={mode} onIonChange={e => setMode(e.detail.value as any)} className="bg-gray-100 p-1 rounded-full">
                <IonSegmentButton value="create" className="rounded-full">
                    <IonLabel className="font-bold normal-case">Crear Grupo</IonLabel>
                </IonSegmentButton>
                <IonSegmentButton value="join" className="rounded-full">
                    <IonLabel className="font-bold normal-case">Unirse</IonLabel>
                </IonSegmentButton>
             </IonSegment>

             <div className="space-y-4">
                 <div className="bg-gray-50 p-4 rounded-2xl border border-gray-100">
                    <label className="text-xs font-bold text-gray-500 uppercase ml-1 block mb-2">Tu Nombre</label>
                    <input 
                        type="text" 
                        value={name}
                        onChange={e => setName(e.target.value)}
                        placeholder="Ej: Angel"
                        className="w-full bg-white p-3 rounded-xl border border-gray-200 font-bold text-lg outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all"
                    />
                 </div>

                 {mode === 'join' && (
                     <div className="bg-gray-50 p-4 rounded-2xl border border-gray-100">
                        <label className="text-xs font-bold text-gray-500 uppercase ml-1 block mb-2">Código del Grupo</label>
                        <input 
                            type="text" 
                            value={code}
                            onChange={e => setCode(e.target.value.toUpperCase())}
                            placeholder="Ej: AB12"
                            className="w-full bg-white p-3 rounded-xl border border-gray-200 font-black text-2xl tracking-widest uppercase outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all text-center placeholder:tracking-normal placeholder:font-medium"
                            maxLength={6}
                        />
                     </div>
                 )}
                 
                 {error && <p className="text-red-500 text-sm text-center font-medium bg-red-50 p-2 rounded-lg">{error}</p>}
                 {!userLocation && <p className="text-amber-600 text-sm text-center bg-amber-50 p-2 rounded-lg">Esperando ubicación GPS...</p>}

                 <button
                    onClick={mode === 'create' ? handleCreate : handleJoin}
                    disabled={isLoading || !name || (!code && mode === 'join') || !userLocation}
                    className={`w-full font-bold py-4 rounded-2xl shadow-lg shadow-blue-200 flex items-center justify-center gap-2 transition-all active:scale-95 ${
                        mode === 'create' 
                        ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                        : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                    } disabled:opacity-50 disabled:grayscale`}
                 >
                    {isLoading ? (
                        <span>Procesando...</span>
                    ) : (
                        <>
                            <IonIcon icon={mode === 'create' ? carSportOutline : searchOutline} />
                            {mode === 'create' ? 'Crear Convoy' : 'Unirse al Convoy'}
                        </>
                    )}
                 </button>
             </div>
          </div>
        )}

      </IonContent>
    </IonModal>
  );
};

export default ConvoyModal;
