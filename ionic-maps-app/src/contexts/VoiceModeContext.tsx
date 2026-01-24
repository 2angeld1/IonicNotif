import React, { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import { getUserSettings, saveUserSettings } from '../services/apiService';
import type { VoiceMode } from '../types';


interface VoiceModeContextType {
  voiceMode: VoiceMode;
  setVoiceMode: (mode: VoiceMode) => void;
  cycleVoiceMode: () => void;
  speak: (text: string, isAlert?: boolean) => void;
}

const VoiceModeContext = createContext<VoiceModeContextType | undefined>(undefined);

const VOICE_MODES: VoiceMode[] = ['all', 'alerts', 'mute'];

export const VoiceModeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [voiceMode, setVoiceMode] = useState<VoiceMode>('all');

  // Cargar configuración al iniciar
  useEffect(() => {
    getUserSettings().then(settings => {
      if (settings) {
        console.log('🔊 Configuración de voz cargada:', settings.voice_mode);
        setVoiceMode(settings.voice_mode);
      }
    });
  }, []);

  // Wrapper para actualizar y guardar
  const handleSetVoiceMode = useCallback((mode: VoiceMode) => {
    setVoiceMode(mode);
    saveUserSettings({ voice_mode: mode });
  }, []);

  const cycleVoiceMode = useCallback(() => {
    setVoiceMode(current => {
      const currentIndex = VOICE_MODES.indexOf(current);
      const nextIndex = (currentIndex + 1) % VOICE_MODES.length;
      const newMode = VOICE_MODES[nextIndex];
      // Guardar en backend
      saveUserSettings({ voice_mode: newMode });
      return newMode;
    });
  }, []);

  const speak = useCallback((text: string, isAlert: boolean = false) => {
    // Si está muteado, no hablar
    if (voiceMode === 'mute') return;
    
    // Si solo alertas y no es alerta, no hablar
    if (voiceMode === 'alerts' && !isAlert) return;
    
    // Hablar
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'es-ES';
      utterance.rate = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  }, [voiceMode]);

  return (
    <VoiceModeContext.Provider value={{ voiceMode, setVoiceMode: handleSetVoiceMode, cycleVoiceMode, speak }}>
      {children}
    </VoiceModeContext.Provider>
  );
};

export const useVoiceMode = (): VoiceModeContextType => {
  const context = useContext(VoiceModeContext);
  if (!context) {
    throw new Error('useVoiceMode must be used within VoiceModeProvider');
  }
  return context;
};

export const getVoiceModeLabel = (mode: VoiceMode): string => {
  switch (mode) {
    case 'all': return 'Voz: Todo';
    case 'alerts': return 'Voz: Alertas';
    case 'mute': return 'Silenciado';
  }
};

export const getVoiceModeIcon = (mode: VoiceMode): string => {
  switch (mode) {
    case 'all': return 'volumeHighOutline';
    case 'alerts': return 'volumeMediumOutline';
    case 'mute': return 'volumeMuteOutline';
  }
};
