'use client';

import { useEffect } from 'react';
import { ClockIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

export default function TimeoutPage() {
  useEffect(() => {
    // Rediriger vers la page d'accueil après 10 secondes
    const timer = setTimeout(() => {
      window.location.href = '/';
    }, 10000);

    return () => clearTimeout(timer);
  }, []);

  const handleReconnect = () => {
    window.location.href = '/';
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="card p-8 w-full max-w-md mx-auto text-center animate-fade-in">
        {/* Icon */}
        <div className="flex justify-center mb-6">
          <div className="bg-yellow-100 p-4 rounded-full">
            <ClockIcon className="h-12 w-12 text-yellow-600" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Session expirée
        </h1>

        {/* Message */}
        <p className="text-gray-600 mb-6">
          Votre session WiFi a expiré en raison d'une inactivité prolongée ou 
          d'un dépassement du temps limite autorisé.
        </p>

        {/* Reconnect Button */}
        <button
          onClick={handleReconnect}
          className="btn-primary w-full flex items-center justify-center mb-4"
        >
          <ArrowPathIcon className="h-5 w-5 mr-2" />
          Se reconnecter
        </button>

        {/* Auto redirect info */}
        <p className="text-sm text-gray-500">
          Redirection automatique dans 10 secondes...
        </p>
      </div>
    </main>
  );
}
