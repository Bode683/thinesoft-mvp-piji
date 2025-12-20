'use client';

import { useState, useEffect } from 'react';
import { ExclamationTriangleIcon, WifiIcon } from '@heroicons/react/24/outline';
import LoginForm from '@/components/LoginForm';
import SuccessPage from '@/components/SuccessPage';
import { SessionManager } from '@/lib/session';
import { ApiService } from '@/lib/api';

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [serviceStatus, setServiceStatus] = useState<boolean | null>(null);

  useEffect(() => {
    // Vérifier le statut du service
    checkServiceHealth();
    
    // Vérifier s'il y a une session active
    const session = SessionManager.getCurrentSession();
    if (session && SessionManager.isSessionValid()) {
      setIsAuthenticated(true);
      // Configurer les gestionnaires de nettoyage
      SessionManager.setupCleanupHandlers();
    }
    
    setIsLoading(false);
  }, []);

  const checkServiceHealth = async () => {
    try {
      const isHealthy = await ApiService.healthCheck();
      setServiceStatus(isHealthy);
    } catch (error) {
      setServiceStatus(false);
    }
  };

  const handleLoginSuccess = () => {
    setError(null);
    setIsAuthenticated(true);
    // Configurer les gestionnaires de nettoyage
    SessionManager.setupCleanupHandlers();
  };

  const handleLoginError = (message: string) => {
    setError(message);
  };

  const handleDisconnect = () => {
    setIsAuthenticated(false);
    setError(null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        {/* Service Status Warning */}
        {serviceStatus === false && (
          <div className="alert-error mb-6 flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
            <span>Service d'authentification indisponible. Veuillez réessayer plus tard.</span>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="alert-error mb-6 flex items-center animate-slide-up">
            <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
            <span>{error}</span>
          </div>
        )}

        {/* Main Content */}
        {isAuthenticated ? (
          <SuccessPage onDisconnect={handleDisconnect} />
        ) : (
          <div className="flex flex-col items-center">
            {/* Welcome Header */}
            <div className="text-center mb-8">
              <div className="flex justify-center mb-4">
                <div className="bg-primary-100 p-4 rounded-full">
                  <WifiIcon className="h-12 w-12 text-primary-600" />
                </div>
              </div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Portail Captif WiFi
              </h1>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Bienvenue sur notre réseau WiFi sécurisé. 
                Veuillez vous authentifier pour accéder à Internet.
              </p>
            </div>

            {/* Login Form */}
            <LoginForm 
              onSuccess={handleLoginSuccess}
              onError={handleLoginError}
            />

            {/* Network Info */}
            <div className="mt-8 text-center">
              <div className="card p-6 max-w-md mx-auto">
                <h3 className="font-semibold text-gray-900 mb-3">
                  Informations du réseau
                </h3>
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>Réseau:</span>
                    <span className="font-medium">WiFi-Secure</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Sécurité:</span>
                    <span className="font-medium">WPA2-Enterprise</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Bande passante:</span>
                    <span className="font-medium">100 Mbps</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="mt-8 text-center text-sm text-gray-500 max-w-md mx-auto">
              <p>
                Ce réseau est surveillé et protégé. L'utilisation est soumise aux 
                conditions d'utilisation et à la politique de confidentialité.
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
