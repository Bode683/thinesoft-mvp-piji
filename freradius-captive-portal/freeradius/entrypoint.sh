#!/bin/bash

# En mode host network, utiliser 127.0.0.1 pour les connexions locales
HOST_IP="127.0.0.1"

echo "Utilisation de l'IP hôte: $HOST_IP"

# Configuration PostgreSQL
echo "$HOST_IP:5432:radius:radius:radiuspass" > /root/.pgpass
chmod 600 /root/.pgpass

# Vérification de la connexion
export PGPASSWORD="radiuspass"
until psql -h $HOST_IP -U radius -d radius -c "SELECT 1" >/dev/null 2>&1; do
    echo "En attente de PostgreSQL sur $HOST_IP..."
    sleep 2
done

echo "PostgreSQL est prêt - démarrage de FreeRADIUS"

# Ajouter host.docker.internal au fichier /etc/hosts
echo "$(ip route | awk '/default/ { print $3 }') host.docker.internal" >> /etc/hosts

# Vérification que radiusd existe
if [ -f /usr/sbin/freeradius ]; then
    echo "Lancement de FreeRADIUS"
    exec /usr/sbin/freeradius -X
else
    echo "ERREUR: FreeRADIUS non trouvé"
    echo "Contenu de /usr/sbin/:"
    ls -la /usr/sbin/
    exit 1
fi