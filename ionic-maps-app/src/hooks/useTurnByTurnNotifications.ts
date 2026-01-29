import { useEffect, useRef } from 'react';
import { LocalNotifications } from '@capacitor/local-notifications';
import { useRouteStepProgress } from './useRouteStepProgress';
import type { RouteStep, LatLng } from '../types';
import { formatDistance } from '../utils/geoUtils';

export const useTurnByTurnNotifications = (
  steps: RouteStep[],
  userLocation: LatLng | null,
  isRouteMode: boolean
) => {
  const { currentStepIndex } = useRouteStepProgress(steps, userLocation);
  const lastNotifiedStep = useRef<number>(-1);
  const hasRequestedPermissions = useRef(false);

  // Solicitar permisos al iniciar ruta
  useEffect(() => {
    const init = async () => {
        if (isRouteMode && !hasRequestedPermissions.current) {
            await LocalNotifications.requestPermissions();
            hasRequestedPermissions.current = true;
        } else if (!isRouteMode) {
            // Cancelar notificación persistente al salir
            await LocalNotifications.cancel({ notifications: [{ id: 1001 }] });
            lastNotifiedStep.current = -1;
        }
    };
    init();
  }, [isRouteMode]);

  // Enviar notificación al cambiar de paso
  useEffect(() => {
    if (!isRouteMode || !steps || steps.length === 0) return;

    const currentStep = steps[currentStepIndex];
    if (!currentStep) return;

    // Solo notificar si cambió el paso actual
    if (currentStepIndex !== lastNotifiedStep.current) {
        const scheduleNotification = async () => {
            try {
                // Cancelamos la anterior para asegurar refresh limpio (opcional, schedule suele sobreescribir)
                // await LocalNotifications.cancel({ notifications: [{ id: 1001 }] });

                await LocalNotifications.schedule({
                    notifications: [{
                        title: currentStep.instruction, // Ej: "Gira a la derecha en Calle 50"
                        body: `Próxima maniobra en ${formatDistance(currentStep.distance)}`,
                        id: 1001,
                        ongoing: true, // Android: No se puede borrar deslizando (Sticky)
                        autoCancel: false,
                        silent: true // Importante para no vibrar/sonar en cada paso si ya habla por voz
                    }]
                });
                console.log('🔔 Notificación de giro enviada:', currentStep.instruction);
            } catch (error) {
                console.error('Error enviando notificación:', error);
            }
        };
        
        scheduleNotification();
        lastNotifiedStep.current = currentStepIndex;
    }
  }, [currentStepIndex, isRouteMode, steps]);
};
