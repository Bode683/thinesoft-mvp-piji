# IAM Stack - Quick Start Guide

## 🚀 Start the Stack

```bash
cd /home/nkem/Desktop/itlds/stack/iam-stack
./scripts/start.sh
```

## 🌐 Access URLs (Updated Ports)

### Keycloak
- **Direct Access**: http://localhost:8080
- **Via Nginx**: http://auth.theddt.local:8880
- **Credentials**: admin / password

### Admin Console
- **URL**: http://localhost:8080/admin
- **Realm**: theddt-realm

### Other Services
- **Grafana**: http://localhost:8881 (admin / admin)
- **Prometheus**: http://localhost:8882
- **pgAdmin**: http://localhost:8883 (admin@example.com / password)
- **phpLDAPadmin**: http://localhost:8884

## 🔧 Configuration Changes

### Development Mode
- Running with `start-dev` command
- HTTP only (no HTTPS/TLS certificates required)
- `KC_HTTP_ENABLED: true`
- `KC_HTTPS_ENABLED: false`

### Port Changes
- Nginx ports changed from 9080-9084 to 8880-8884
- Keycloak direct access on port 8080
- Avoids conflicts with other nginx instances

### Fixed Issues
1. ✅ Removed HTTPS certificate requirements
2. ✅ Fixed pgAdmin email validation (changed from admin@keycloak.local to admin@example.com)
3. ✅ Updated health check to work with dev mode
4. ✅ Added direct port access for Keycloak (8080)
5. ✅ Changed Nginx ports to avoid conflicts

## 📝 Quick Commands

```bash
# Start services
./scripts/start.sh

# Stop services
./scripts/stop.sh

# View logs
docker logs iam-keycloak -f
docker logs iam-postgres -f

# Check status
docker compose ps

# Restart Keycloak only
docker compose restart keycloak
```

## 🧪 Test Keycloak

```bash
# Health check
curl http://localhost:8080/health/ready

# Get admin token
curl -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=password"
```

## 🔍 Troubleshooting

### Keycloak not starting
```bash
docker logs iam-keycloak -f
docker exec iam-keycloak curl http://localhost:8080/health/ready
```

### Check PostgreSQL
```bash
docker exec iam-postgres pg_isready -U keycloak -d keycloak
```

### Restart everything
```bash
docker compose down
docker compose up -d
```
