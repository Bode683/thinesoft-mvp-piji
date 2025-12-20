# Configuration Mode Host Network

## Vue d'ensemble

La stack RADIUS a été configurée en **mode host network** pour permettre une intégration directe avec votre borne WiFi EAP 110. En mode host, les conteneurs Docker utilisent directement l'interface réseau de la machine hôte, ce qui élimine les problèmes de NAT et de routage.

## Avantages du Mode Host

✅ **Intégration directe** : Les services sont accessibles directement sur l'IP de votre machine  
✅ **Pas de NAT** : Élimination des problèmes de translation d'adresses  
✅ **Performance optimale** : Pas de couche réseau supplémentaire  
✅ **Configuration simplifiée** : L'EAP 110 peut accéder directement aux services  

## Architecture Réseau

```
EAP 110 (192.168.1.132) ←→ Machine Hôte (192.168.1.144) ←→ Conteneurs Docker
                                    ↓
                            Services directement accessibles:
                            - FreeRADIUS: 1812/1813 UDP
                            - Backend API: 8000 TCP
                            - Portail Captif: 3000 TCP
                            - PgAdmin: 8084 TCP
                            - PostgreSQL: 5432 TCP
```

## Services et Ports

| Service | Port | Protocole | Accès |
|---------|------|-----------|--------|
| FreeRADIUS Auth | 1812 | UDP | EAP 110 → Machine Hôte |
| FreeRADIUS Acct | 1813 | UDP | EAP 110 → Machine Hôte |
| Backend API | 8000 | TCP | Portail Captif → Machine Hôte |
| Portail Captif | 3000 | TCP | Utilisateurs → Machine Hôte |
| PostgreSQL | 5432 | TCP | Services internes |
| PgAdmin | 8084 | TCP | Administration |

## Configuration EAP 110

### RADIUS Server Settings
```
Primary Server IP: 192.168.1.144
Authentication Port: 1812
Accounting Port: 1813
Shared Secret: testing123
```

### Captive Portal Settings
```
Portal Type: External
Redirect URL: http://192.168.1.144:3000
Authentication Method: RADIUS
```

## Démarrage de la Stack

### Méthode 1 : Script automatique
```bash
./start_system_host_mode.sh
```

### Méthode 2 : Docker Compose manuel
```bash
# Arrêter les services existants
docker-compose down

# Démarrer en mode host
docker-compose up --build -d

# Vérifier l'état
docker-compose ps
```

## Vérification de la Connectivité

### Tests depuis la machine hôte
```bash
# Test PostgreSQL
nc -z localhost 5432

# Test Backend API
curl http://localhost:8000/health

# Test FreeRADIUS Auth
echo "User-Name = testuser, User-Password = testpass123" | \
radclient -x localhost:1812 auth testing123

# Test FreeRADIUS Accounting
echo "User-Name = testuser, Acct-Status-Type = Start, Acct-Session-Id = test123" | \
radclient -x localhost:1813 acct testing123
```

### Tests depuis le réseau
```bash
# Remplacer 192.168.1.144 par l'IP de votre machine
curl http://192.168.1.144:8000/health
curl http://192.168.1.144:3000
```

## URLs d'Accès

### Depuis la machine hôte
- 🌐 Portail Captif: http://localhost:3000
- 🔧 API Backend: http://localhost:8000
- 📊 PgAdmin: http://localhost:8084

### Depuis le réseau (remplacer par votre IP)
- 🌐 Portail Captif: http://192.168.1.144:3000
- 🔧 API Backend: http://192.168.1.144:8000
- 📊 PgAdmin: http://192.168.1.144:8084

## Sécurité et Firewall

### Ports à ouvrir sur la machine hôte
```bash
# FreeRADIUS
sudo ufw allow 1812/udp
sudo ufw allow 1813/udp

# Services web (si accès externe requis)
sudo ufw allow 3000/tcp  # Portail Captif
sudo ufw allow 8000/tcp  # Backend API
sudo ufw allow 8084/tcp  # PgAdmin (optionnel)
```

### Restriction d'accès (optionnel)
```bash
# Limiter l'accès au réseau local uniquement
sudo ufw allow from 192.168.1.0/24 to any port 1812
sudo ufw allow from 192.168.1.0/24 to any port 1813
sudo ufw allow from 192.168.1.0/24 to any port 3000
```

## Dépannage

### Problèmes de connectivité
1. **Vérifier que les services sont démarrés**
   ```bash
   docker-compose ps
   ```

2. **Vérifier les ports en écoute**
   ```bash
   netstat -tlnup | grep -E "(1812|1813|3000|8000|8084|5432)"
   ```

3. **Vérifier les logs**
   ```bash
   docker-compose logs freeradius
   docker-compose logs backend
   docker-compose logs captive-portal
   ```

### Conflits de ports
Si vous avez des services existants sur les mêmes ports :
```bash
# Identifier les processus utilisant les ports
sudo lsof -i :1812
sudo lsof -i :1813
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :5432

# Arrêter les services conflictuels si nécessaire
sudo systemctl stop [service-name]
```

### Problèmes de résolution DNS
En mode host, les conteneurs ne peuvent plus se résoudre par nom. Les variables d'environnement ont été mises à jour pour utiliser `localhost` :
- `RADIUS_SERVER=localhost`
- `DATABASE_URL=postgresql://radius:radiuspass@localhost:5432/radius`
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`

## Retour au Mode Bridge

Si vous souhaitez revenir au mode bridge réseau :
```bash
git checkout docker-compose.yml
docker-compose down
docker-compose up --build -d
```

## Monitoring et Logs

### Surveillance en temps réel
```bash
# Logs de tous les services
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f freeradius
docker-compose logs -f backend
docker-compose logs -f captive-portal
```

### Métriques système
```bash
# Utilisation des ressources
docker stats

# État détaillé des conteneurs
docker-compose ps -a
```

## Support et Dépannage

En cas de problème :
1. Vérifiez les logs des services
2. Testez la connectivité réseau
3. Vérifiez la configuration du firewall
4. Consultez la documentation EAP 110 pour la configuration RADIUS

La configuration en mode host offre une intégration optimale avec votre infrastructure réseau existante.
