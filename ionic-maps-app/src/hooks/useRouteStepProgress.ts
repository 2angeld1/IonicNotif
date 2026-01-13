import { useState, useEffect, useCallback } from 'react';
import { calculateDistance } from '../utils/geoUtils';
import type { RouteStep, LatLng } from '../types';

export const useRouteStepProgress = (steps: RouteStep[], userLocation: LatLng | null | undefined) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [distanceToNextStep, setDistanceToNextStep] = useState<number | null>(null);

  const playNotificationSound = useCallback(() => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.5);

      gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);

      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      oscillator.start();
      oscillator.stop(audioCtx.currentTime + 0.5);
    } catch (e) {
      // Audio no disponible
    }
  }, []);

  useEffect(() => {
    if (!userLocation || !steps[currentStepIndex]) return;

    const currentStep = steps[currentStepIndex];
    if (currentStep.location) {
      const distance = calculateDistance(
        userLocation.lat,
        userLocation.lng,
        currentStep.location.lat,
        currentStep.location.lng
      );
      setDistanceToNextStep(distance);

      if (distance < 30 && currentStepIndex < steps.length - 1) {
        playNotificationSound();
        setCurrentStepIndex(prev => prev + 1);
      }
    }
  }, [userLocation, steps, currentStepIndex, playNotificationSound]);

  useEffect(() => {
    if (currentStepIndex > 0) {
      playNotificationSound();
    }
  }, [currentStepIndex, playNotificationSound]);

  const goToNextStep = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex(prev => prev + 1);
    }
  };

  const goToPreviousStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
    }
  };

  return {
    currentStepIndex,
    distanceToNextStep,
    goToNextStep,
    goToPreviousStep,
    playNotificationSound
  };
};
