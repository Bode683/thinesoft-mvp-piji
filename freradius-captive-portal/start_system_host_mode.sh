#!/bin/bash

# Script de démarrage pour la stack RADIUS en mode host network
# Cela permet l'intégration directe avec l'EAP 110 sur le même réseau

set -e

echo "🚀 Démarrage de la stack RADIUS en mode host network..."
echo "📡 Les conteneurs seront accessibles directement sur le réseau de l'hôte"

# Vérifier que Docker est démarré
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker n'est pas démarré. Veuillez démarrer Docker d'abord."
    exit 1
fi

# Arrêter les conteneurs existants
echo "🛑 Arrêt des conteneurs existants..."
docker compose down --remove-orphans

# Nettoyer les volumes si demandé
if [ "$1" = "--clean" ]; then
    echo "🧹 Nettoyage des volumes..."
    docker compose down -v
    docker system prune -f
fi

# Construire et démarrer les services
echo "🔨 Construction et démarrage des services..."
docker compose up --build -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 10

# Vérifier l'état des services
echo "📊 État des services:"
docker compose ps

# Vérifier la connectivité des services
echo "🔍 Vérification de la connectivité..."

# Vérifier PostgreSQL
if nc -z localhost 5432 2>/dev/null; then
    echo "✅ PostgreSQL: Accessible sur localhost:5432"
else
    echo "❌ PostgreSQL: Non accessible"
fi

# Vérifier Backend API
if nc -z localhost 8000 2>/dev/null; then
    echo "✅ Backend API: Accessible sur localhost:8000"
else
    echo "❌ Backend API: Non accessible"
fi

# Vérifier FreeRADIUS
if nc -u -z localhost 1812 2>/dev/null; then
    echo "✅ FreeRADIUS Auth: Accessible sur localhost:1812/udp"
else
    echo "❌ FreeRADIUS Auth: Non accessible"
fi

if nc -u -z localhost 1813 2>/dev/null; then
    echo "✅ FreeRADIUS Acct: Accessible sur localhost:1813/udp"
else
    echo "❌ FreeRADIUS Acct: Non accessible"
fi

# Vérifier Portail Captif
if nc -z localhost 3000 2>/dev/null; then
    echo "✅ Portail Captif: Accessible sur localhost:3000"
else
    echo "❌ Portail Captif: Non accessible"
fi

# Vérifier PgAdmin
if nc -z localhost 8084 2>/dev/null; then
    echo "✅ PgAdmin: Accessible sur localhost:8084"
else
    echo "❌ PgAdmin: Non accessible"
fi

echo ""
echo "🎉 Stack RADIUS démarrée en mode host network!"
echo ""
echo "📍 URLs d'accès (depuis n'importe quelle machine du réseau):"
echo "   🌐 Portail Captif: http://$(hostname -I | awk '{print $1}'):3000"
echo "   🔧 API Backend: http://$(hostname -I | awk '{print $1}'):8000"
echo "   📊 PgAdmin: http://$(hostname -I | awk '{print $1}'):8084"
echo "   🔐 RADIUS Auth: $(hostname -I | awk '{print $1}'):1812/udp"
echo "   📈 RADIUS Acct: $(hostname -I | awk '{print $1}'):1813/udp"
echo ""
echo "🔑 Credentials de test:"
echo "   👤 Utilisateur: testuser / testpass123"
echo "   📊 PgAdmin: admin@radius.com / admin123"
echo ""
echo "⚙️  Configuration EAP 110:"
echo "   📡 RADIUS Server IP: $(hostname -I | awk '{print $1}')"
echo "   🔐 Auth Port: 1812"
echo "   📈 Acct Port: 1813"
echo "   🔑 Shared Secret: testing123"
echo "   🌐 Captive Portal URL: http://$(hostname -I | awk '{print $1}'):3000"
echo ""
echo "📋 Pour voir les logs: docker compose logs -f [service]"
echo "🛑 Pour arrêter: docker compose down"
