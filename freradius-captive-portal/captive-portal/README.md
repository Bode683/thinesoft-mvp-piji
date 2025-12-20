# Portail Captif WiFi

Un portail captif moderne développé avec Next.js 14 et TypeScript, intégré à une stack d'authentification RADIUS avec FreeRADIUS et PostgreSQL.

## Fonctionnalités

### 🔐 Authentification
- Interface utilisateur moderne et responsive
- Authentification RADIUS sécurisée
- Validation en temps réel des credentials
- Gestion d'erreurs complète

### 📊 Gestion de session
- Sessions automatiques avec cookies sécurisés
- Heartbeat périodique (Interim-Update RADIUS)
- Détection d'inactivité automatique
- Déconnexion propre avec Accounting Stop

### 🎨 Interface utilisateur
- Design moderne avec Tailwind CSS
- Animations fluides et transitions
- Interface responsive (mobile-first)
- Indicateurs de statut en temps réel

### 🔧 Fonctionnalités avancées
- Timer de session avec compte à rebours
- Informations de connexion détaillées
- Déconnexion manuelle et automatique
- Gestion des timeouts de session

## Architecture

```
Utilisateur WiFi → Portail Captif (Next.js) → Backend API (FastAPI) → PostgreSQL
                                    ↓
                              FreeRADIUS (Auth/Acct)
```

## Technologies utilisées

- **Frontend**: Next.js 14, React 18, TypeScript
- **Styling**: Tailwind CSS, Heroicons
- **HTTP Client**: Axios
- **Session Management**: js-cookie
- **Build**: Docker multi-stage

## Installation

### Prérequis
- Docker et Docker Compose
- Node.js 18+ (pour le développement local)

### Démarrage avec Docker
```bash
# Depuis la racine du projet
docker compose up -d captive-portal
```

### Développement local
```bash
cd captive-portal
npm install
npm run dev
```

## Configuration

### Variables d'environnement
- `NEXT_PUBLIC_API_URL`: URL de l'API backend (défaut: http://localhost:8000/api/v1)

### Intégration réseau
Le portail captif est conçu pour être intégré avec :
- Points d'accès WiFi compatibles
- Serveurs RADIUS (FreeRADIUS)
- Systèmes de gestion réseau

## Utilisation

### Flux d'authentification
1. L'utilisateur se connecte au réseau WiFi
2. Redirection automatique vers le portail captif
3. Saisie des credentials d'authentification
4. Validation RADIUS via l'API backend
5. Création de session et accès Internet
6. Monitoring continu de la session
7. Déconnexion automatique ou manuelle

### Gestion des sessions
- **Durée**: Configurable via les attributs RADIUS
- **Heartbeat**: Interim-Update toutes les 30 secondes
- **Timeout inactivité**: 5 minutes par défaut
- **Nettoyage**: Accounting Stop automatique

## API Endpoints utilisés

- `POST /api/v1/auth/radius` - Authentification
- `POST /api/v1/accounting/radius` - Accounting RADIUS
- `GET /api/v1/auth/health` - Vérification de santé

## Sécurité

- Validation côté client et serveur
- Cookies sécurisés avec SameSite
- Headers de sécurité (CSP, X-Frame-Options)
- Gestion des timeouts de session
- Nettoyage automatique des sessions

## Monitoring

Le portail inclut :
- Indicateurs de statut de connexion
- Timer de session en temps réel
- Informations de bande passante
- Logs détaillés des sessions

## Déploiement

### Production
```bash
# Build et démarrage
docker compose up -d

# Vérification des logs
docker compose logs captive-portal
```

### Configuration réseau
Pour un déploiement en production :
1. Configurer le point d'accès pour rediriger vers le portail
2. Ajuster les variables d'environnement
3. Configurer les certificats SSL si nécessaire
4. Tester l'intégration RADIUS

## Développement

### Structure du projet
```
src/
├── app/                 # Pages Next.js (App Router)
├── components/          # Composants React
├── lib/                # Utilitaires (API, session)
├── types/              # Types TypeScript
└── styles/             # Styles globaux
```

### Scripts disponibles
- `npm run dev` - Serveur de développement
- `npm run build` - Build de production
- `npm run start` - Serveur de production
- `npm run lint` - Linting ESLint

## Support

Pour des questions ou des problèmes :
1. Vérifier les logs Docker
2. Tester la connectivité API
3. Valider la configuration RADIUS
4. Consulter la documentation FreeRADIUS
