# Production-Grade IAM Stack with Keycloak

A complete, production-ready Identity and Access Management (IAM) platform using Keycloak with PostgreSQL, LDAP federation, and comprehensive observability.

## 🏗️ Architecture

### Core Components

- **Keycloak 23.0** - Identity and Access Management server
- **PostgreSQL 15** - Database backend
- **Nginx** - Reverse proxy with custom ports
- **OpenLDAP** - Directory service for user federation
- **Prometheus** - Metrics collection
- **Grafana** - Observability dashboards
- **pgAdmin** - Database management
- **phpLDAPadmin** - LDAP management interface

### Network Architecture

- **Network**: `iam-network` (172.20.0.0/16)
- **Nginx Reverse Proxy**: Port 9080-9084
- All services communicate via internal Docker network
- External access through Nginx only

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### 1. Setup Hosts File

Add these entries to `/etc/hosts`:

```bash
sudo bash -c 'cat >> /etc/hosts << EOF
127.0.0.1 auth.theddt.local
127.0.0.1 grafana.theddt.local
127.0.0.1 prometheus.theddt.local
127.0.0.1 pgadmin.theddt.local
127.0.0.1 ldap.theddt.local
EOF'
```

### 2. Configure Environment

The `.env` file is already configured. Review and update passwords if needed:

```bash
nano .env
```

### 3. Make Scripts Executable

```bash
chmod +x scripts/*.sh
```

### 4. Start the Stack

```bash
./scripts/start.sh
```

The startup script will:
- Start PostgreSQL and wait for it to be ready
- Start Keycloak and import the realm
- Start OpenLDAP with sample users
- Start observability stack (Prometheus, Grafana)
- Start management tools (pgAdmin, phpLDAPadmin)
- Start Nginx reverse proxy

---

## 🌐 Access Points

All services are accessible through Nginx on custom ports:

| Service | URL | Port | Credentials |
|---------|-----|------|-------------|
| **Keycloak** | http://localhost:8080 (Direct) | 8080 | admin / password |
| **Keycloak** | http://auth.theddt.local:8880 (Nginx) | 8880 | admin / password |
| **Grafana** | http://localhost:8881 | 8881 | admin / admin |
| **Prometheus** | http://localhost:8882 | 8882 | - |
| **pgAdmin** | http://localhost:8883 | 8883 | admin@example.com / password |
| **phpLDAPadmin** | http://localhost:8884 | 8884 | cn=admin,dc=theddt,dc=local / admin123 |

### Direct Service Access (Internal)

These ports are also available for direct access:

- PostgreSQL: `localhost:5432`
- OpenLDAP: `localhost:389` (LDAP), `localhost:636` (LDAPS)

---

## 📋 Pre-configured Resources

### Keycloak Realm: `theddt-realm`

#### Users

| Username | Password | Email | Roles | Group |
|----------|----------|-------|-------|-------|
| admin | admin123 | admin@theddt.local | admin, user | Administrators |
| john.doe | password123 | john.doe@theddt.local | developer, user | Developers |
| jane.smith | password123 | jane.smith@theddt.local | manager, user | Managers |
| bob.wilson | password123 | bob.wilson@theddt.local | user | Users |
| alice.johnson | password123 | alice.johnson@theddt.local | viewer | Users |

#### Roles

- **admin** - Full administrative access
- **developer** - Development access
- **manager** - Management access
- **user** - Standard user access
- **viewer** - Read-only access

#### Clients

- **web-app** - Web application client (confidential)
- **mobile-app** - Mobile application client (public)
- **service-account** - Service account for backend services
- **api-client** - REST API client

### OpenLDAP Directory

**Base DN**: `dc=theddt,dc=local`

#### Sample Users (in LDAP)

| Username | Department | Email | Employee ID |
|----------|------------|-------|-------------|
| michael.chen | Engineering | michael.chen@theddt.local | ENG001 |
| sarah.lee | Engineering | sarah.lee@theddt.local | ENG002 |
| david.kumar | Engineering | david.kumar@theddt.local | ENG003 |
| emily.brown | Sales | emily.brown@theddt.local | SAL001 |
| robert.taylor | Sales | robert.taylor@theddt.local | SAL002 |
| lisa.martinez | HR | lisa.martinez@theddt.local | HR001 |
| james.anderson | HR | james.anderson@theddt.local | HR002 |
| jennifer.white | IT | jennifer.white@theddt.local | IT001 |
| thomas.garcia | IT | thomas.garcia@theddt.local | IT002 |

---

## 🔧 Configuration

### Nginx Reverse Proxy

Nginx is configured to proxy all services with the following features:

- **Custom ports**: 9080-9084 (avoiding conflicts with default ports)
- **Load balancing**: Connection pooling for backend services
- **Security headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **WebSocket support**: For Grafana live updates
- **Compression**: Gzip enabled for better performance
- **Logging**: Separate access/error logs per service

Configuration files:
- `config/nginx/nginx.conf` - Main Nginx configuration
- `config/nginx/conf.d/iam.conf` - IAM stack proxy configuration

### LDAP Federation

To configure LDAP federation in Keycloak:

1. Access Keycloak Admin Console
2. Navigate to: **User Federation** → **Add provider** → **ldap**
3. Use the Postman collection `07-federation-identity-providers.postman_collection.json`
4. Or configure manually with these settings:

```
Connection URL: ldap://openldap:389
Users DN: ou=People,dc=theddt,dc=local
Bind DN: cn=admin,dc=theddt,dc=local
Bind Credential: admin123
```

---

## 📡 API Testing with Postman

### Postman Collections

Located in `postman/` directory:

1. **01-authentication-token-management** - Authentication flows
2. **02-user-management** - User CRUD operations
3. **03-role-management** - Role management
4. **04-client-management** - Client configuration
5. **05-group-management** - Group operations
6. **06-realm-management** - Realm configuration
7. **07-federation-identity-providers** - LDAP/IdP integration
8. **08-sessions-events** - Session and event management

### Import to Postman

1. Open Postman
2. Click **Import**
3. Select all JSON files from `postman/` directory
4. Import the environment: `keycloak-iam.postman_environment.json`
5. Select the environment in Postman
6. Run "Admin Token - Get Access Token" first

### Quick API Test

```bash
# Get admin token
curl -X POST "http://localhost:8080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=password"

# List users
curl -X GET "http://localhost:8080/admin/realms/theddt-realm/users" \
  -H "Authorization: Bearer <access-token>"
```

---

## 📊 Monitoring & Observability

### Prometheus Metrics

Access Prometheus at http://localhost:9082

**Available metrics:**
- Keycloak metrics: `http://keycloak:8080/metrics`
- PostgreSQL metrics: `http://postgres-exporter:9187/metrics`
- System metrics: `http://node-exporter:9100/metrics`

### Grafana Dashboards

Access Grafana at http://localhost:9081

Pre-configured dashboards:
- Keycloak Performance Dashboard
- PostgreSQL Database Metrics
- System Resource Monitoring

**Default credentials**: admin / admin

---

## 🛠️ Management Scripts

### Start Services

```bash
./scripts/start.sh
```

Starts all services in the correct order with health checks.

### Stop Services

```bash
./scripts/stop.sh
```

Gracefully stops all services. Data is preserved in Docker volumes.

### View Logs

```bash
# All services
./scripts/logs.sh

# Specific service
./scripts/logs.sh keycloak
./scripts/logs.sh postgres
./scripts/logs.sh openldap
./scripts/logs.sh nginx
```

### Backup

```bash
./scripts/backup.sh
```

Creates a compressed backup of:
- PostgreSQL database
- Keycloak realm configuration
- OpenLDAP configuration

Backups are stored in `backups/` directory.

### Restore

```bash
./scripts/restore.sh <backup-file.tar.gz>
```

Restores from a previous backup.

### Cleanup

```bash
./scripts/cleanup.sh
```

⚠️ **WARNING**: Removes all containers, volumes, and data. Cannot be undone.

---

## 📚 Documentation

- **Implementation Plan**: `docs/IMPLEMENTATION_PLAN.md`
- **API Documentation**: `docs/API_DOCUMENTATION.md`
- **Postman Collections**: `postman/`

---

## 🔍 Troubleshooting

### Keycloak not starting

```bash
# Check logs
docker logs iam-keycloak -f

# Verify PostgreSQL is ready
docker exec iam-postgres pg_isready -U keycloak
```

### Nginx connection errors

```bash
# Check Nginx logs
docker logs iam-nginx -f

# Verify backend services are running
docker ps | grep iam-

# Test Nginx configuration
docker exec iam-nginx nginx -t
```

### LDAP connection issues

```bash
# Check OpenLDAP logs
docker logs iam-openldap -f

# Test LDAP connection
ldapsearch -x -H ldap://localhost:389 -b "dc=theddt,dc=local" -D "cn=admin,dc=theddt,dc=local" -w admin123
```

### Port conflicts

If ports 8880-8884 are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
nginx:
  ports:
    - "8880:80"      # Change 8880 to another port
    - "8881:9081"    # Change 8881 to another port
    # etc.
```

### Reset everything

```bash
./scripts/cleanup.sh
./scripts/start.sh
```

---

## 🔐 Security Considerations

### Current Setup (Development)

- **HTTP only (no TLS/SSL)** - Running in dev mode with `start-dev`
- **Default passwords** - Change in `.env` file
- **Permissive CORS settings**
- **Debug logging enabled**
- **Direct port access** - Keycloak accessible on port 8080

### Production Recommendations

1. **Enable HTTPS**
   - Generate SSL certificates
   - Update Nginx configuration
   - Configure Keycloak for HTTPS

2. **Change all default passwords**
   - Update `.env` file
   - Use strong, unique passwords
   - Consider using secrets management

3. **Restrict network access**
   - Use firewall rules
   - Limit exposed ports
   - Configure proper CORS policies

4. **Enable audit logging**
   - Already enabled in Keycloak
   - Configure log retention
   - Set up log aggregation

5. **Regular backups**
   - Automate backup script
   - Store backups securely
   - Test restore procedures

6. **Update regularly**
   - Monitor security advisories
   - Update Docker images
   - Apply security patches

---

## 🧪 Testing

### Test LDAP Federation

1. Configure LDAP provider in Keycloak
2. Sync users: Use Postman collection or Admin Console
3. Test login with LDAP user (e.g., michael.chen / password123)

### Test API Operations

1. Import Postman collections
2. Get admin token
3. Run collection tests
4. Verify operations in Admin Console

### Load Testing

Use K6 or Apache Bench for load testing:

```bash
# Install K6
# Create test script
# Run load test against Keycloak
```

---

## 📦 Project Structure

```
iam-stack/
├── config/
│   ├── grafana/          # Grafana dashboards and datasources
│   ├── keycloak/         # Realm configurations
│   ├── nginx/            # Nginx reverse proxy config
│   ├── openldap/         # LDAP schemas and users
│   ├── pgadmin/          # Database connection config
│   └── prometheus/       # Metrics collection config
├── docs/
│   ├── API_DOCUMENTATION.md
│   └── IMPLEMENTATION_PLAN.md
├── postman/              # API collections
├── scripts/              # Management scripts
├── backups/              # Backup storage
├── docker-compose.yml    # Service definitions
├── .env                  # Environment variables
└── README.md            # This file
```

---

## 🤝 Contributing

This is a production-grade IAM stack template. Customize as needed for your use case.

---

## 📄 License

This project configuration is provided as-is for educational and development purposes.

---

## 🆘 Support

For issues:
1. Check logs: `./scripts/logs.sh <service>`
2. Review documentation in `docs/`
3. Verify configuration in `docker-compose.yml`
4. Check Keycloak documentation: https://www.keycloak.org/documentation

---

## 🎯 Next Steps

1. ✅ Start the stack: `./scripts/start.sh`
2. ✅ Access Keycloak Admin Console
3. ✅ Import Postman collections
4. ✅ Configure LDAP federation
5. ✅ Test API operations
6. ✅ Set up monitoring dashboards
7. ✅ Configure backup automation
8. 🔒 Implement TLS/SSL (when ready)
9. 🔒 Harden security settings
10. 🚀 Deploy to production

---

**Built with ❤️ for secure identity management**
