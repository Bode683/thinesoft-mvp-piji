'use client';

import { useState } from 'react';
import { EyeIcon, EyeSlashIcon, WifiIcon, LockClosedIcon, UserIcon } from '@heroicons/react/24/outline';
import { ApiService } from '@/lib/api';
import { SessionManager } from '@/lib/session';
import { AuthRequest } from '@/types';

interface LoginFormProps {
  onSuccess: () => void;
  onError: (message: string) => void;
}

export default function LoginForm({ onSuccess, onError }: LoginFormProps) {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.username.trim() || !formData.password.trim()) {
      onError('Veuillez remplir tous les champs');
      return;
    }

    setIsLoading(true);

    try {
      const authRequest: AuthRequest = {
        username: formData.username.trim(),
        password: formData.password,
        nas_ip_address: '192.168.1.1',
        nas_identifier: 'captive-portal',
        service_type: 'Framed-User',
      };

      const response = await ApiService.authenticate(authRequest);

      if (response['control:Auth-Type'] === 'Accept') {
        // Créer la session
        const timeout = response['reply:Session-Timeout'] 
          ? parseInt(response['reply:Session-Timeout']) 
          : 3600;
        
        SessionManager.createSession(
          formData.username,
          response['reply:Framed-IP-Address'],
          timeout
        );

        onSuccess();
      } else {
        onError(response['reply:Reply-Message'] || 'Authentification échouée');
      }
    } catch (error: any) {
      onError(error.message || 'Erreur de connexion');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  return (
    <div className="card p-8 w-full max-w-md mx-auto animate-fade-in">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex justify-center mb-4">
          <div className="bg-primary-100 p-3 rounded-full">
            <WifiIcon className="h-8 w-8 text-primary-600" />
          </div>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Connexion WiFi
        </h1>
        <p className="text-gray-600">
          Connectez-vous pour accéder à Internet
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Username Field */}
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
            Nom d'utilisateur
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <UserIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              className="input-field pl-10"
              placeholder="Entrez votre nom d'utilisateur"
              required
              disabled={isLoading}
              autoComplete="username"
            />
          </div>
        </div>

        {/* Password Field */}
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
            Mot de passe
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <LockClosedIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className="input-field pl-10 pr-10"
              placeholder="Entrez votre mot de passe"
              required
              disabled={isLoading}
              autoComplete="current-password"
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              onClick={() => setShowPassword(!showPassword)}
              disabled={isLoading}
            >
              {showPassword ? (
                <EyeSlashIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              ) : (
                <EyeIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              )}
            </button>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary w-full flex items-center justify-center"
        >
          {isLoading ? (
            <>
              <div className="spinner mr-2"></div>
              Connexion en cours...
            </>
          ) : (
            <>
              <WifiIcon className="h-5 w-5 mr-2" />
              Se connecter
            </>
          )}
        </button>
      </form>

      {/* Footer */}
      <div className="mt-6 text-center">
        <p className="text-xs text-gray-500">
          En vous connectant, vous acceptez les conditions d'utilisation du réseau WiFi.
        </p>
      </div>
    </div>
  );
}
