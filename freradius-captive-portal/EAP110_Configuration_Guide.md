# Guide de Configuration TP-Link EAP 110 avec Portail Captif

## 🔧 Informations de votre configuration

- **Adresse IP de votre serveur** : `192.168.1.144`
- **Adresse IP EAP 110** : `192.168.1.132`
- **URL portail captif** : `http://192.168.1.144:3000`
- **Secret RADIUS** : `testing123`

## 📋 Étapes de configuration sur l'EAP 110

### 1. Accès à l'interface d'administration
1. Ouvrez votre navigateur et allez sur : `http://192.168.1.132`
2. Connectez-vous avec vos identifiants administrateur

### 2. Configuration du SSID
1. Allez dans **Wireless** → **SSIDs**
2. Créez un nouveau SSID ou modifiez un existant :
   - **SSID Name** : `WiFi-Captive` (ou votre nom préféré)
   - **Wireless Security** : `None` ou `Open` (pour le portail captif)
   - **Portal** : `Enable`
   - **Portal Type** : `External`

### 3. Configuration du serveur RADIUS
1. Allez dans **Authentication** → **RADIUS**
2. Configurez le serveur RADIUS primaire :
   - **Primary RADIUS Server IP** : `192.168.1.144`
   - **Primary RADIUS Port** : `1812`
   - **Primary RADIUS Shared Secret** : `testing123`

### 4. Configuration de l'Accounting RADIUS
1. Dans la même section RADIUS :
   - **Primary Accounting Server IP** : `192.168.1.144`
   - **Primary Accounting Port** : `1813`
   - **Primary Accounting Shared Secret** : `testing123`
   - **Accounting** : `Enable`

### 5. Configuration du Portail Captif
1. Allez dans **Portal** → **Portal Settings**
2. Configurez :
   - **Portal Status** : `Enable`
   - **Portal Type** : `External`
   - **External Portal Server URL** : `http://192.168.1.144:3000`
   - **Authentication Method** : `External RADIUS Server`
   - **Redirect URL** : `http://192.168.1.144:3000`

### 6. Paramètres de session (optionnel)
- **Session Timeout** : `3600` secondes (1 heure)
- **Idle Timeout** : `300` secondes (5 minutes)
- **Force HTTPS** : `Disable` (pour les tests)

## 🧪 Test de la configuration

### Credentials de test
- **Utilisateur** : `testuser`
- **Mot de passe** : `testpass123`

### Procédure de test
1. Connectez un appareil (smartphone, ordinateur) au WiFi `WiFi-Captive`
2. Ouvrez un navigateur web
3. Vous devriez être automatiquement redirigé vers `http://192.168.1.144:3000`
4. Saisissez les credentials de test
5. Après authentification, vous devriez avoir accès à Internet

## 🔍 Dépannage

### Le portail captif ne s'affiche pas
1. **Vérifiez la connectivité réseau** :
   ```bash
   ping 192.168.1.144  # Depuis un appareil connecté au WiFi
   ```

2. **Testez l'accès direct au portail** :
   - Ouvrez manuellement : `http://192.168.1.144:3000`

3. **Vérifiez la configuration DNS** :
   - L'EAP 110 doit rediriger le trafic DNS vers le portail captif

### Problèmes d'authentification RADIUS
1. **Testez RADIUS depuis le serveur** :
   ```bash
   echo "User-Name = testuser, User-Password = testpass123" | radclient -x 192.168.1.144:1812 auth testing123
   ```

2. **Vérifiez les logs** :
   ```bash
   docker compose logs -f freeradius
   docker compose logs -f backend
   ```

### Configuration alternative si le portail ne s'affiche pas

Si le portail captif ne s'affiche pas automatiquement, essayez cette configuration :

1. **Dans l'EAP 110, section Portal** :
   - **Portal Type** : `Internal`
   - **Authentication Method** : `External RADIUS Server`
   - **Success URL** : `http://192.168.1.144:3000/success`
   - **Failure URL** : `http://192.168.1.144:3000`

2. **Ou utilisez la redirection manuelle** :
   - Configurez une page de redirection HTML simple
   - Pointez vers votre portail captif

## 📊 Monitoring et administration

### URLs utiles
- **Portail captif** : http://192.168.1.144:3000
- **Panel d'administration** : http://192.168.1.144:3000/admin
- **API Backend** : http://192.168.1.144:8000
- **PgAdmin** : http://192.168.1.144:8084

### Commandes de monitoring
```bash
# Voir les sessions actives
curl http://192.168.1.144:8000/api/v1/accounting/sessions/active

# Voir les statistiques
curl http://192.168.1.144:8000/api/v1/accounting/stats

# Logs en temps réel
docker compose logs -f
```

## 🚨 Points importants

1. **Sécurité** : Le secret RADIUS `testing123` est pour les tests. Changez-le en production.
2. **Réseau** : Assurez-vous que l'EAP 110 peut joindre votre serveur sur les ports 1812/1813 UDP et 3000 TCP.
3. **Firewall** : Vérifiez que les ports sont ouverts sur votre serveur.
4. **DNS** : L'EAP 110 doit pouvoir résoudre l'adresse IP de votre serveur.

## 🔧 Configuration avancée

### Si vous voulez utiliser HTTPS
1. Configurez un certificat SSL
2. Modifiez l'URL du portail vers `https://192.168.1.144:3000`
3. Ajoutez le port 443 dans docker-compose.override.yml

### Pour un environnement de production
1. Changez le secret RADIUS
2. Configurez des certificats SSL
3. Utilisez des mots de passe forts
4. Configurez la sauvegarde de la base de données
5. Mettez en place le monitoring des logs
