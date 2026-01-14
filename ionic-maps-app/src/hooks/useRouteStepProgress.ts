import { useState, useEffect, useCallback, useRef } from 'react';
import { calculateDistance } from '../utils/geoUtils';
import { sendNotification, requestNotificationPermission } from '../services/notificationService';
import type { RouteStep, LatLng } from '../types';

const STEP_COMPLETE_THRESHOLD = 35; // metros para considerar que pasaste el paso
const APPROACHING_THRESHOLD = 100; // metros para avisar que te acercas

export const useRouteStepProgress = (steps: RouteStep[], userLocation: LatLng | null | undefined) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [distanceToNextStep, setDistanceToNextStep] = useState<number | null>(null);
  const [isApproaching, setIsApproaching] = useState(false);

  // Referencias para evitar notificaciones duplicadas
  const notifiedStepsRef = useRef<Set<number>>(new Set());
  const approachNotifiedRef = useRef<Set<number>>(new Set());
  const lastDistanceRef = useRef<number>(Infinity);

  // Pedir permiso de notificaciones al montar
  useEffect(() => {
    requestNotificationPermission();
  }, []);

  // Reset cuando cambian los pasos (nueva ruta)
  useEffect(() => {
    setCurrentStepIndex(0);
    setDistanceToNextStep(null);
    setIsApproaching(false);
    notifiedStepsRef.current.clear();
    approachNotifiedRef.current.clear();
    lastDistanceRef.current = Infinity;
  }, [steps]);

  const playNotificationSound = useCallback(() => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.5);

      gainNode.gain.setValueAtTime(0.15, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);

      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      oscillator.start();
      oscillator.stop(audioCtx.currentTime + 0.5);
    } catch (e) {
      // Audio no disponible
    }
  }, []);

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

        // Notificación de acercamiento
        sendNotification(`📍 En ${Math.round(distanceToCurrent)}m`, {
          body: currentStep.instruction,
          tag: 'nav-approaching',
          silent: false,
        });
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
          sendNotification(`➡️ ${nextStep.instruction}`, {
            body: `Próximo paso en ${Math.round(nextStep.distance)}m`,
            tag: 'nav-step',
            renotify: true,
            requireInteraction: false,
          });

          setCurrentStepIndex(prev => prev + 1);
        } else {
          // Llegamos al destino
          sendNotification('🎉 ¡Has llegado a tu destino!', {
            body: 'Tu viaje ha terminado',
            tag: 'nav-arrived',
            requireInteraction: true,
          });
        }
      }
    }

    lastDistanceRef.current = distanceToCurrent;
  }, [userLocation, steps, currentStepIndex, playNotificationSound]);

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
    playNotificationSound
  };
};
