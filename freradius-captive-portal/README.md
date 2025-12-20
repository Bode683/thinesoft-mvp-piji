# Portail Captif avec FreeRADIUS

## Vue d'ensemble

Ce projet implémente un système de portail captif complet intégrant FreeRADIUS pour l'authentification et l'accounting des utilisateurs WiFi. Le système est composé de 4 services Docker orchestrés pour fournir une solution robuste de gestion d'accès réseau.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Utilisateur   │────│ Portail Captif │────│   Backend API   │
│     WiFi        │    │   (Next.js)     │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   FreeRADIUS    │────│   PostgreSQL    │
                       │   (Auth/Acct)   │    │  (Base données) │
                       └─────────────────┘    └─────────────────┘
```

### Services

1. **FreeRADIUS** (ports 1812-1813 UDP, 8080 TCP)
   - Serveur d'authentification RADIUS
   - Gestion des sessions utilisateur
   - Accounting des connexions

2. **Backend API** (port 8000)
   - API FastAPI pour l'authentification
   - Gestion des sessions d'accounting
   - Interface REST pour FreeRADIUS

3. **PostgreSQL** (port 5432)
   - Base de données RADIUS standard
   - Stockage des utilisateurs et sessions
   - Historique des connexions

4. **Portail Captif** (port 3000)
   - Interface Next.js pour l'authentification
   - Gestion des sessions côté client
   - Heartbeat automatique et déconnexion

## Fonctionnalités

### ✅ Authentification
- Authentification utilisateur via portail web
- Validation des credentials via FreeRADIUS
- Support des attributs RADIUS personnalisés

### ✅ Gestion des sessions
- Démarrage automatique des sessions d'accounting
- Heartbeat périodique (Interim-Update)
- Détection de déconnexion automatique
- Nettoyage des sessions expirées

### ✅ Monitoring
- Sessions actives en temps réel
- Statistiques de bande passante
- Logs détaillés des événements
- API de monitoring

### ✅ Sécurité
- Validation des sessions
- Timeouts configurables
- Gestion d'erreurs robuste
- Nettoyage automatique des ressources

## Installation et démarrage

### Prérequis
- Docker et Docker Compose
- Python 3.8+ (pour les tests)
- Ports 3000, 8000, 5432, 1812-1813 disponibles

### Démarrage rapide

```bash
# Cloner le projet
git clone <repository-url>
cd stable-004

# Démarrer tous les services
./start_system.sh

# Tester le système
python3 test_system.py
```

### Démarrage manuel

```bash
# Construire et démarrer les services
docker-compose up -d

# Vérifier l'état
docker-compose ps

# Voir les logs
docker-compose logs -f
```

## Configuration

### Variables d'environnement

```bash
# Backend
DATABASE_URL=postgresql://radius:radiuspass@postgres:5432/radius
REDIS_URL=redis://redis:6379/0

# FreeRADIUS
RADIUS_SECRET=testing123
RADIUS_DB_HOST=postgres
RADIUS_DB_USER=radius
RADIUS_DB_PASS=radiuspass

# Portail Captif
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Utilisateurs de test

Par défaut, les utilisateurs suivants sont disponibles :
- `testuser` / `testpass`
- `admin` / `admin123`

## API Endpoints

### Authentification
- `POST /api/v1/auth/authenticate` - Authentification utilisateur
- `POST /api/v1/auth/authorize` - Autorisation RADIUS

### Accounting
- `POST /api/v1/accounting/radius` - Événements d'accounting RADIUS
- `GET /api/v1/accounting/active-sessions` - Sessions actives
- `GET /api/v1/accounting/session-status/{session_id}` - Statut d'une session

### Monitoring
- `GET /health` - Santé du service
- `GET /api/v1/accounting/bandwidth-stats` - Statistiques de bande passante
- `GET /api/v1/accounting/nas-list` - Liste des NAS

## Tests

### Test automatique complet
```bash
python3 test_system.py
```

### Tests manuels

#### Test d'authentification
```bash
curl -X POST http://localhost:8000/api/v1/auth/authenticate \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass",
    "nas_ip_address": "192.168.1.1",
    "nas_identifier": "test-nas"
  }'
```

#### Test d'accounting
```bash
curl -X POST http://localhost:8000/api/v1/accounting/radius \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "session_id": "test-session-123",
    "status_type": "Start",
    "nas_ip_address": "192.168.1.1",
    "nas_identifier": "test-nas"
  }'
```

## Utilisation

### Flux d'authentification

1. **Connexion WiFi** : L'utilisateur se connecte au réseau WiFi
2. **Redirection** : Il est redirigé vers le portail captif (http://localhost:3000)
3. **Authentification** : Saisie des identifiants sur le portail
4. **Validation** : Le backend valide via FreeRADIUS
5. **Session** : Démarrage de la session d'accounting
6. **Accès** : L'utilisateur obtient l'accès Internet
7. **Monitoring** : Heartbeat périodique pour maintenir la session
8. **Déconnexion** : Arrêt automatique ou manuel de la session

### Gestion des sessions

Le système gère automatiquement :
- **Démarrage** : Session d'accounting au login
- **Maintenance** : Heartbeat toutes les 30 secondes
- **Timeout** : Déconnexion après 5 minutes d'inactivité
- **Nettoyage** : Suppression des sessions expirées

## Monitoring et logs

### Logs en temps réel
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f backend
docker-compose logs -f freeradius
```

### Sessions actives
```bash
curl http://localhost:8000/api/v1/accounting/active-sessions
```

### Statistiques
```bash
curl http://localhost:8000/api/v1/accounting/bandwidth-stats
```

## Dépannage

### Problèmes courants

#### Services ne démarrent pas
```bash
# Vérifier l'état
docker-compose ps

# Redémarrer un service
docker-compose restart backend

# Reconstruire les images
docker-compose build --no-cache
```

#### Erreurs de base de données
```bash
# Réinitialiser la base
docker-compose down -v
docker-compose up -d
```

#### Problèmes de réseau
```bash
# Vérifier la connectivité
docker-compose exec backend ping postgres
docker-compose exec freeradius ping backend
```

### Logs de débogage

#### Backend
```bash
docker-compose logs -f backend | grep ERROR
```

#### FreeRADIUS
```bash
docker-compose exec freeradius radiusd -X
```

## Développement

### Structure du projet
```
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/v1/         # Endpoints API
│   │   ├── models/         # Modèles SQLAlchemy
│   │   └── services/       # Services métier
│   └── requirements.txt
├── captive-portal/         # Interface Next.js
│   ├── app/               # Pages Next.js
│   ├── lib/               # Utilitaires
│   └── package.json
├── freeradius/            # Configuration FreeRADIUS
│   ├── mods-available/    # Modules disponibles
│   └── sites-available/   # Sites virtuels
├── postgres/              # Scripts SQL
└── docker-compose.yml     # Orchestration
```

### Ajout de fonctionnalités

1. **Backend** : Ajouter des endpoints dans `backend/app/api/v1/`
2. **Frontend** : Créer des pages dans `captive-portal/app/`
3. **FreeRADIUS** : Modifier la configuration dans `freeradius/`
4. **Base de données** : Ajouter des migrations dans `postgres/`

## Sécurité

### Recommandations de production

1. **Secrets** : Utiliser des secrets forts et uniques
2. **HTTPS** : Activer TLS pour tous les services web
3. **Firewall** : Restreindre l'accès aux ports sensibles
4. **Monitoring** : Surveiller les tentatives d'intrusion
5. **Backup** : Sauvegarder régulièrement la base de données

### Configuration sécurisée

```bash
# Générer des secrets forts
openssl rand -hex 32  # Pour les clés de session
openssl rand -hex 16  # Pour les secrets RADIUS
```

## Support

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FreeRADIUS Documentation](https://freeradius.org/documentation/)
- [Next.js Documentation](https://nextjs.org/docs)

### Contribution
1. Fork le projet
2. Créer une branche feature
3. Commiter les changements
4. Pousser vers la branche
5. Créer une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
