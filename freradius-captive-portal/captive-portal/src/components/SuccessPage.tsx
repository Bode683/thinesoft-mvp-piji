'use client';

import { useState, useEffect } from 'react';
import { 
  CheckCircleIcon, 
  WifiIcon, 
  ClockIcon, 
  SignalIcon,
  ArrowRightOnRectangleIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { SessionManager } from '@/lib/session';
import { SessionInfo } from '@/types';

interface SuccessPageProps {
  onDisconnect: () => void;
}

export default function SuccessPage({ onDisconnect }: SuccessPageProps) {
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [sessionDuration, setSessionDuration] = useState<number>(0);

  useEffect(() => {
    // Récupérer les informations de session
    const currentSession = SessionManager.getCurrentSession();
    if (currentSession) {
      setSession(currentSession);
    }

    // Timer pour mettre à jour le temps restant et la durée
    const timer = setInterval(() => {
      if (currentSession) {
        const now = Date.now();
        const elapsed = Math.floor((now - currentSession.startTime.getTime()) / 1000);
        const remaining = Math.max(0, (currentSession.timeout || 3600) - elapsed);
        
        setSessionDuration(elapsed);
        setTimeRemaining(remaining);

        // Rediriger si la session a expiré
        if (remaining <= 0) {
          handleDisconnect();
        }
      }
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleDisconnect = async () => {
    try {
      await SessionManager.endSession();
      onDisconnect();
    } catch (error) {
      console.error('Error during disconnect:', error);
      onDisconnect();
    }
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const getSignalStrength = (): number => {
    // Simulation de la force du signal (dans un vrai déploiement, ceci viendrait du système)
    return Math.floor(Math.random() * 2) + 3; // 3-4 barres
  };

  if (!session) {
    return (
      <div className="card p-8 w-full max-w-md mx-auto">
        <div className="text-center">
          <p className="text-gray-600">Chargement des informations de session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6 animate-fade-in">
      {/* Success Header */}
      <div className="card p-8 text-center">
        <div className="flex justify-center mb-4">
          <CheckCircleIcon className="h-16 w-16 text-success-500" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Connexion réussie !
        </h1>
        <p className="text-gray-600 text-lg">
          Bienvenue <span className="font-semibold text-primary-600">{session.username}</span>
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Vous êtes maintenant connecté à Internet
        </p>
      </div>

      {/* Session Info */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Connection Status */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <WifiIcon className="h-6 w-6 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">État de la connexion</h2>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Statut</span>
              <div className="flex items-center">
                <div className="w-2 h-2 bg-success-500 rounded-full mr-2"></div>
                <span className="text-success-600 font-medium">Connecté</span>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Signal</span>
              <div className="flex items-center">
                <SignalIcon className="h-4 w-4 text-gray-400 mr-1" />
                <div className="flex space-x-1">
                  {[1, 2, 3, 4].map((bar) => (
                    <div
                      key={bar}
                      className={`w-1 h-3 rounded-sm ${
                        bar <= getSignalStrength() 
                          ? 'bg-success-500' 
                          : 'bg-gray-300'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>

            {session.ipAddress && (
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Adresse IP</span>
                <span className="font-mono text-sm text-gray-900">{session.ipAddress}</span>
              </div>
            )}
          </div>
        </div>

        {/* Session Timer */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <ClockIcon className="h-6 w-6 text-primary-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Temps de session</h2>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Temps écoulé</span>
              <span className="font-mono text-lg text-primary-600">
                {formatTime(sessionDuration)}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Temps restant</span>
              <span className={`font-mono text-lg ${
                timeRemaining < 300 ? 'text-danger-600' : 'text-success-600'
              }`}>
                {formatTime(timeRemaining)}
              </span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-1000 ${
                  timeRemaining < 300 ? 'bg-danger-500' : 'bg-success-500'
                }`}
                style={{ 
                  width: `${(timeRemaining / (session.timeout || 3600)) * 100}%` 
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Session Details */}
      <div className="card p-6">
        <div className="flex items-center mb-4">
          <ChartBarIcon className="h-6 w-6 text-primary-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">Détails de la session</h2>
        </div>
        
        <div className="grid md:grid-cols-2 gap-4 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">ID de session</span>
            <span className="font-mono text-gray-900">{session.sessionId.slice(-8)}</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-600">Heure de connexion</span>
            <span className="text-gray-900">
              {session.startTime.toLocaleTimeString('fr-FR')}
            </span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-600">Utilisateur</span>
            <span className="text-gray-900">{session.username}</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-600">Type de service</span>
            <span className="text-gray-900">Accès Internet</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={handleDisconnect}
            className="btn-secondary flex items-center justify-center flex-1"
          >
            <ArrowRightOnRectangleIcon className="h-5 w-5 mr-2" />
            Se déconnecter
          </button>
          
          <button
            onClick={() => window.open('https://www.google.com', '_blank')}
            className="btn-primary flex items-center justify-center flex-1"
          >
            <WifiIcon className="h-5 w-5 mr-2" />
            Naviguer sur Internet
          </button>
        </div>
        
        <p className="text-xs text-gray-500 text-center mt-4">
          Vous serez automatiquement déconnecté à la fin de votre session ou en cas d'inactivité prolongée.
        </p>
      </div>
    </div>
  );
}
