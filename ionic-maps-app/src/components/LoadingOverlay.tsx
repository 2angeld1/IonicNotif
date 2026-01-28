import React from 'react';

interface LoadingOverlayProps {
  isLoading: boolean;
  message: string;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ isLoading, message }) => {
  if (!isLoading) return null;

  return (
    <div className="fixed inset-0 z-[10000] flex flex-col items-center justify-center bg-white/80 backdrop-blur-xl text-center">
      <div className="w-24 h-24 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <h2 className="mt-8 text-2xl font-bold text-gray-800">Ionic Notif</h2>
      <p className="mt-2 text-gray-500 font-medium">{message}</p>
    </div>
  );
};

export default LoadingOverlay;
