import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { calculateDistance } from '../utils/geoUtils';
import { sendNotification, requestNotificationPermission } from '../services/notificationService';
import { useVoiceMode } from '../contexts/VoiceModeContext';
import type { RouteStep, LatLng } from '../types';

const STEP_COMPLETE_THRESHOLD = 35; // metros para considerar que pasaste el paso
const APPROACHING_THRESHOLD = 100; // metros para avisar que te acercas

export const useRouteStepProgress = (steps: RouteStep[], userLocation: LatLng | null | undefined) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [distanceToNextStep, setDistanceToNextStep] = useState<number | null>(null);
  const [isApproaching, setIsApproaching] = useState(false);

  // Usar el contexto de voz centralizado
  const { speak: contextSpeak } = useVoiceMode();

  // Referencias para evitar notificaciones duplicadas
  const notifiedStepsRef = useRef<Set<number>>(new Set());
  const approachNotifiedRef = useRef<Set<number>>(new Set());
  const lastDistanceRef = useRef<number>(Infinity);

  // Crear una clave única basada en el contenido de los pasos
  // Esto detecta cuando los pasos cambian incluso si la referencia del array es la misma
  const stepsKey = useMemo(() => {
    if (!steps.length) return '';
    return steps.map(s => `${s.instruction}|${s.distance}|${s.location?.lat}|${s.location?.lng}`).join(';');
  }, [steps]);

  // Pedir permiso de notificaciones al montar
  useEffect(() => {
    requestNotificationPermission();
  }, []);

  // Reset cuando cambian los pasos (nueva ruta o recálculo)
  useEffect(() => {
    console.log('[useRouteStepProgress] Resetting due to steps change');
    setCurrentStepIndex(0);
    setDistanceToNextStep(null);
    setIsApproaching(false);
    notifiedStepsRef.current.clear();
    approachNotifiedRef.current.clear();
    lastDistanceRef.current = Infinity;
  }, [stepsKey]);

  // Wrapper para speak: paso a paso NO es alerta
  const speak = useCallback((text: string, isAlert: boolean = false) => {
    contextSpeak(text, isAlert);
  }, [contextSpeak]);

  const playNotificationSound = useCallback(() => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      oscillator.type = 'sine';
      // Tono fijo más limpio (subtle ding)
      oscillator.frequency.setValueAtTime(980, audioCtx.currentTime);

      // Envolvente de volumen suave
      gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.6);

      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      oscillator.start();
      oscillator.stop(audioCtx.currentTime + 0.5);
    } catch (e) {
      // Audio no disponible
    }
  }, []);

  // Reset cuando cambian los pasos (nueva ruta o recálculo)
  useEffect(() => {
    console.log('[useRouteStepProgress] Resetting due to steps change');
    setCurrentStepIndex(0);
    setDistanceToNextStep(null);
    setIsApproaching(false);
    notifiedStepsRef.current.clear();
    approachNotifiedRef.current.clear();
    lastDistanceRef.current = Infinity;
    // Opcional: Anunciar inicio
    // if (steps.length > 0) speak(`Iniciando ruta. ${steps[0].instruction}`);
  }, [stepsKey, speak]); // Agregamos speak a dep

  // Detectar progreso en la ruta
  useEffect(() => {
    if (!userLocation || !steps.length || currentStepIndex >= steps.length) return;

    const currentStep = steps[currentStepIndex];
    if (!currentStep.location) return;

    // Calcular distancia al punto de maniobra del paso actual
    const distanceToCurrent = calculateDistance(
      userLocation.lat,
      userLocation.lng,
      currentStep.location.lat,
      currentStep.location.lng
    );

    setDistanceToNextStep(distanceToCurrent);

    // Detectar si nos estamos acercando (para aviso previo)
    if (distanceToCurrent < APPROACHING_THRESHOLD && distanceToCurrent > STEP_COMPLETE_THRESHOLD) {
      if (!approachNotifiedRef.current.has(currentStepIndex)) {
        setIsApproaching(true);
        approachNotifiedRef.current.add(currentStepIndex);

        // Notificación de acercamiento VISUAL
        sendNotification(`📍 En ${Math.round(distanceToCurrent)}m`, {
          body: currentStep.instruction,
          tag: 'nav-approaching',
          silent: false,
        });

        // Notificación de VOZ
        speak(`En ${Math.round(distanceToCurrent)} metros, ${currentStep.instruction.toLowerCase()}`);
      }
    }

    // Detectar si hemos completado el paso
    // Condiciones: estamos cerca Y nos estamos alejando (ya pasamos)
    const isMovingAway = distanceToCurrent > lastDistanceRef.current;
    const isCloseEnough = distanceToCurrent < STEP_COMPLETE_THRESHOLD;

    if (isCloseEnough || (distanceToCurrent < APPROACHING_THRESHOLD / 2 && isMovingAway)) {
      if (!notifiedStepsRef.current.has(currentStepIndex)) {
        notifiedStepsRef.current.add(currentStepIndex);
        setIsApproaching(false);

        // Avanzar al siguiente paso
        if (currentStepIndex < steps.length - 1) {
          playNotificationSound();

          const nextStep = steps[currentStepIndex + 1];
          // Notificación visual
          sendNotification(`➡️ ${nextStep.instruction}`, {
            body: `Próximo paso en ${Math.round(nextStep.distance)}m`,
            tag: 'nav-step',
            renotify: true,
            requireInteraction: false,
          });

          // VOZ: Instrucción inmediata del nuevo paso
          // Ejemplo: "Continúa recto por 2 kilómetros"
          speak(nextStep.instruction);

          setCurrentStepIndex(prev => prev + 1);
        } else {
          // Llegamos al destino
          sendNotification('🎉 ¡Has llegado a tu destino!', {
            body: 'Tu viaje ha terminado',
            tag: 'nav-arrived',
            requireInteraction: true,
          });
          speak('Has llegado a tu destino. Felicidades.', true); // true = es alerta
        }
      }
    }

    lastDistanceRef.current = distanceToCurrent;
  }, [userLocation, steps, currentStepIndex, playNotificationSound, speak]);

  const goToNextStep = useCallback(() => {
    if (currentStepIndex < steps.length - 1) {
      notifiedStepsRef.current.add(currentStepIndex);
      setCurrentStepIndex(prev => prev + 1);
      playNotificationSound();
    }
  }, [currentStepIndex, steps.length, playNotificationSound]);

  const goToPreviousStep = useCallback(() => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
    }
  }, [currentStepIndex]);

  return {
    currentStepIndex,
    distanceToNextStep,
    isApproaching,
    goToNextStep,
    goToPreviousStep,
    playNotificationSound,
    speak // Exportamos speak por si acaso
  };
};
