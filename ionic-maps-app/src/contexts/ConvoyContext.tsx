import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import type { Convoy, LatLng } from '../types';
import { createConvoy, joinConvoy, updateConvoyLocation, getConvoyStatus } from '../services/apiService';

interface ConvoyContextType {
  convoy: Convoy | null;
  userId: string | null;
  create: (hostName: string, location: LatLng) => Promise<boolean>;
  join: (code: string, userName: string, location: LatLng) => Promise<boolean>;
  leave: () => void;
  updateLocation: (location: LatLng) => Promise<void>;
}

const ConvoyContext = createContext<ConvoyContextType | undefined>(undefined);

export const ConvoyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [convoy, setConvoy] = useState<Convoy | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  
  const convoyRef = useRef<Convoy | null>(null);
  const userIdRef = useRef<string | null>(null);

  useEffect(() => {
    convoyRef.current = convoy;
    userIdRef.current = userId;
  }, [convoy, userId]);
  
  const create = useCallback(async (hostName: string, location: LatLng) => {
    const result = await createConvoy(hostName, location);
    if (result) {
      setConvoy(result);
      setUserId(result.host_id);
      return true;
    }
    return false;
  }, []);

  const join = useCallback(async (code: string, userName: string, location: LatLng) => {
    const result = await joinConvoy(code, userName, location);
    if (result) {
      setConvoy(result.convoy);
      setUserId(result.user_id);
      return true;
    }
    return false;
  }, []);

  const leave = useCallback(() => {
    setConvoy(null);
    setUserId(null);
  }, []);

  const updateLocation = useCallback(async (location: LatLng) => {
    if (!convoyRef.current || !userIdRef.current) return;
    
    // Llamada al backend para actualizar mi posición
    // El backend retorna el estado actualizado del convoy
    const updated = await updateConvoyLocation(convoyRef.current._id, userIdRef.current, location);
    if (updated) {
       // OJO: Si actualizamos setConvoy aquí, disparamos re-render, que dispara useEffect en HomePage, que llama updateLocation de nuevo...
       // PERO como updateLocation ahora es estable (no depende de convoy), el useEffect de HomePage NO se dispara infinitamente
       // SIEMPRE QUE el useEffect de HomePage solo dependa de [userLocation, updateLocation]
       setConvoy(updated);
    }
  }, []);

  // Polling para sincronizar el estado del convoy (ver a otros usuarios)
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    if (convoy?._id) {
      // Sondear cada 4 segundos
      interval = setInterval(async () => {
        // Solo obtener si el convoy sigue activo
        try {
            const updated = await getConvoyStatus(convoy._id);
            if (updated) {
                 setConvoy(updated);
            }
        } catch (e) {
            console.error("Error polling convoy", e);
        }
      }, 4000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [convoy?._id]);

  return (
    <ConvoyContext.Provider value={{ convoy, userId, create, join, leave, updateLocation }}>
      {children}
    </ConvoyContext.Provider>
  );
};

export const useConvoy = () => {
  const context = useContext(ConvoyContext);
  if (context === undefined) {
    throw new Error('useConvoy must be used within a ConvoyProvider');
  }
  return context;
};
