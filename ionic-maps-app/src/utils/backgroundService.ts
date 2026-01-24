/**
 * Reproduce un audio silencioso en bucle para mantener la PWA activa en segundo plano.
 * Esto evita que el navegador suspenda la ejecución de JS (GPS y TTS) al minimizar.
 */

let audioContext: AudioContext | null = null;
let silenceOscillator: OscillatorNode | null = null;

export const startBackgroundKeepAlive = () => {
  try {
    if (!audioContext) {
      audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    }

    if (audioContext.state === 'suspended') {
      audioContext.resume();
    }

    // Si ya hay uno sonando, no hacemos nada
    if (silenceOscillator) return;

    // Crear oscilador silencioso
    silenceOscillator = audioContext.createOscillator();
    // Frecuencia inaudible (o muy baja si el dispositivo filtra frecuencias altas)
    // Usamos 0.01Hz para que sea inaudible pero el sistema detecte actividad
    silenceOscillator.frequency.setValueAtTime(0.01, audioContext.currentTime); 
    
    // Gain casi cero, pero no cero absoluto para evitar optimizaciones que corten el sonido
    const gainNode = audioContext.createGain();
    gainNode.gain.setValueAtTime(0.01, audioContext.currentTime);

    silenceOscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    silenceOscillator.start();
    
    // Configurar Media Session para mostrar controles en la pantalla de bloqueo (opcional, ayuda a mantenerlo vivo)
    if ('mediaSession' in navigator) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: 'Navegación Activa',
        artist: 'Ionic Maps',
        album: 'Ruta en curso',
        artwork: [
            { src: '/icon-192.png', sizes: '192x192', type: 'image/png' }
        ]
      });
      navigator.mediaSession.playbackState = 'playing';
    }

    console.log('[BackgroundService] Keep-alive audio started');
  } catch (e) {
    console.warn('[BackgroundService] Failed to start keep-alive', e);
  }
};

export const stopBackgroundKeepAlive = () => {
  try {
    if (silenceOscillator) {
      silenceOscillator.stop();
      silenceOscillator.disconnect();
      silenceOscillator = null;
    }
    
    if (audioContext) {
      // No cerramos el contexto para poder reusarlo, pero podemos suspenderlo
      // audioContext.suspend(); 
    }

    if ('mediaSession' in navigator) {
      navigator.mediaSession.playbackState = 'none';
    }
    
    console.log('[BackgroundService] Keep-alive audio stopped');
  } catch (e) {
    console.error(e);
  }
};

// ============== WAKE LOCK (MANTENER PANTALLA ENCENDIDA) ==============

let wakeLock: any = null; // Usamos any para evitar problemas de tipado si Typescript no tiene WakeLockSentinel

export const requestWakeLock = async () => {
  // Solo intentar si el navegador lo soporta
  if ('wakeLock' in navigator) {
    try {
      wakeLock = await (navigator as any).wakeLock.request('screen');
      console.log('💡 Pantalla mantenida encendida (Wake Lock active)');

      wakeLock.addEventListener('release', () => {
        console.log('💡 Wake Lock liberado por el sistema');
      });
    } catch (err: any) {
      console.warn(`⚠️ No se pudo activar Wake Lock: ${err.name}, ${err.message}`);
    }
  } else {
    console.log('⚠️ Wake Lock API no soportada en este navegador');
  }
};

export const releaseWakeLock = async () => {
  if (wakeLock) {
    try {
      await wakeLock.release();
      wakeLock = null;
      console.log('💡 Pantalla liberada (Wake Lock released)');
    } catch (err: any) {
      console.error(`Error liberando Wake Lock: ${err.name}, ${err.message}`);
    }
  }
};

// Re-solicitar el bloqueo si la app vuelve a primer plano (visibilidad)
document.addEventListener('visibilitychange', async () => {
  if (wakeLock !== null && document.visibilityState === 'visible') {
    // Si teníamos un lock y volvemos a ser visibles, pedirlo de nuevo
    await requestWakeLock();
  }
});
