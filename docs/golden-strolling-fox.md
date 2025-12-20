# Docker Infrastructure Setup Plan

## Overview
Set up Docker infrastructure for the microservices architecture with minimal Dockerfiles (base images only) and a comprehensive docker-compose.yml that allows downloading all images via `docker compose pull` before full implementation.

## Services Architecture

### Core Microservices
1. **PKaKey** - PKI Platform Service (Python/Django/DRF/Wagtail)
2. **PeSequel** - Database & API Service (PostgreSQL/PostgREST)
3. **QueWall** - API Gateway & Authentication (Traefik/Keycloak)
4. **KoolFlows** - Workflow Service (minimal/future)

### Infrastructure Components

#### QueWall Dependencies
- `quewall_traefik` - Traefik v2.10 (reverse proxy)
- `quewall_keycloak` - Keycloak 23.0 (OIDC identity provider)
- `quewall_postgres` - PostgreSQL 15 (Keycloak database)
- `quewall_oauth2_proxy` - oauth2-proxy (ForwardAuth middleware)

#### PeSequel Dependencies
- `pesequel_postgres` - PostgreSQL 15 (primary database)
- `pesequel_postgrest` - PostgREST (auto-generated REST API)
- `pesequel_pgbouncer` - pgBouncer (connection pooling)
- `pesequel_pgadmin` - pgAdmin 4 (database management UI)

#### PKaKey Dependencies
- `pkakey_postgres` - PostgreSQL 15 (PKaKey database)
- `pkakey_redis` - Redis 7 (cache and message broker)
- `pkakey_django` - Django/Wagtail application (custom build)
- `pkakey_celery_worker` - Celery worker (uses pkakey_django image)
- `pkakey_celery_beat` - Celery beat scheduler (uses pkakey_django image)

## Directory Structure to Create

```
C:\Users\nkema\Desktop\itlds\mvp\
├── docker-compose.yml                    # Main orchestration file
├── .env.example                          # Environment variables template
├── .dockerignore                         # Global Docker ignore patterns
├── README.md                             # Docker setup documentation
│
├── PKaKey\                               # [EXISTS - will add files]
│   ├── Dockerfile                        # NEW: Python 3.11 base image
│   ├── requirements.txt                  # NEW: Empty placeholder
│   └── .dockerignore                     # NEW: Python-specific ignores
│
├── PeSequel\                             # [EXISTS - will add files]
│   └── .dockerignore                     # NEW: SQL-specific ignores
│
├── QueWall\                              # [CREATE NEW]
│   ├── traefik\
│   │   └── .gitkeep                      # Placeholder for future config
│   ├── keycloak\
│   │   └── .gitkeep                      # Placeholder for future realm config
│   └── .dockerignore                     # NEW: Config-specific ignores
│
└── KoolFlows\                            # [CREATE NEW]
    └── .dockerignore                     # NEW: General ignores
```

## Files to Create

### 1. Root Configuration Files

#### `docker-compose.yml`
- Define all 14 services with appropriate base images
- Configure 5 Docker networks: `web`, `backend`, `pkakey_net`, `pesequel_net`, `quewall_net`
- Define 11 named volumes for data persistence
- Set up service dependencies and health checks
- Configure Traefik labels for routing
- Environment variable placeholders

**Services grouped by startup order:**
1. Infrastructure: All PostgreSQL instances, Redis
2. Gateway: Traefik, Keycloak (depends on quewall_postgres)
3. Auth: oauth2-proxy (depends on Keycloak)
4. Data layer: pgBouncer, PostgREST, pgAdmin
5. Application: PKaKey Django, Celery workers

#### `.env.example`
Environment variables for:
- Database credentials (3 PostgreSQL instances)
- Keycloak admin credentials
- OAuth2 proxy configuration
- Django secret key
- Domain settings (theddt.local)
- Debug flags for development

#### `.dockerignore`
Global patterns:
- Git files (.git/, .gitignore)
- IDE files (.vscode/, .idea/)
- Python cache (__pycache__/, *.pyc)
- Node modules
- Documentation (docs/)
- Environment files (.env)

#### `README.md`
Documentation covering:
- Quick start guide
- Prerequisites (Docker, Docker Compose)
- DNS configuration (add theddt.local to hosts file)
- Service access URLs
- Troubleshooting common issues

### 2. PKaKey Service Files

#### `PKaKey/Dockerfile`
```dockerfile
FROM python:3.11-slim
# Full Django/Wagtail implementation will be added later
WORKDIR /app
```

#### `PKaKey/requirements.txt`
Empty file (placeholder for future dependencies)

#### `PKaKey/.dockerignore`
Python-specific patterns

### 3. Service Directory Files

#### `PeSequel/.dockerignore`
SQL and database-specific patterns

#### `QueWall/.dockerignore`
Configuration file patterns

#### `KoolFlows/.dockerignore`
General ignore patterns

## Docker Networks Strategy

1. **web** - Public-facing services (Traefik, all HTTP services)
2. **backend** - Internal service communication
3. **pkakey_net** - PKaKey service isolation
4. **pesequel_net** - PeSequel service isolation
5. **quewall_net** - QueWall service isolation

## Docker Volumes Strategy

**PKaKey volumes:**
- `pkakey_postgres_data` - PostgreSQL data persistence
- `pkakey_redis_data` - Redis persistence
- `pkakey_media` - Django media files
- `pkakey_static` - Django static files

**PeSequel volumes:**
- `pesequel_postgres_data` - PostgreSQL data persistence
- `pgadmin_data` - pgAdmin settings

**QueWall volumes:**
- `keycloak_postgres_data` - Keycloak database
- `traefik_acme` - TLS certificates (future)
- `traefik_logs` - Access logs

## Docker Images to Download

| Service | Image | Size (approx) |
|---------|-------|---------------|
| PostgreSQL (3 instances) | `postgres:15-alpine` | ~80 MB each |
| Redis | `redis:7-alpine` | ~30 MB |
| Python | `python:3.11-slim` | ~130 MB |
| Traefik | `traefik:v2.10` | ~100 MB |
| Keycloak | `quay.io/keycloak/keycloak:23.0` | ~400 MB |
| oauth2-proxy | `quay.io/oauth2-proxy/oauth2-proxy:latest` | ~25 MB |
| PostgREST | `postgrest/postgrest:latest` | ~20 MB |
| pgBouncer | `pgbouncer/pgbouncer:latest` | ~10 MB |
| pgAdmin | `dpage/pgadmin4:latest` | ~400 MB |

**Total download size:** ~1.5 GB

## Service Routing (via Traefik)

| URL | Service | Description |
|-----|---------|-------------|
| `theddt.local` | Traefik dashboard | Main entry point (dev mode) |
| `keycloak.theddt.local` | Keycloak | Identity provider admin UI |
| `auth.theddt.local` | oauth2-proxy | Authentication service |
| `api.theddt.local` | PostgREST | Auto-generated REST API |
| `pgadmin.theddt.local` | pgAdmin | Database management UI |
| `pkakey.theddt.local` | PKaKey Django | PKI platform (future) |

## Implementation Steps

### Step 1: Create Directory Structure
- Create `QueWall/` folder with subdirectories
- Create `KoolFlows/` folder
- Add `.gitkeep` files in empty directories

### Step 2: Create Configuration Files
- Write `docker-compose.yml` with all service definitions
- Write `.env.example` with all environment variables
- Write root `.dockerignore`
- Write `README.md` with setup instructions

### Step 3: Create Service Files
- Write `PKaKey/Dockerfile` (minimal, just base image)
- Write `PKaKey/requirements.txt` (empty placeholder)
- Write `.dockerignore` for each service folder

### Step 4: Verification
- Validate docker-compose.yml syntax
- Ensure all referenced paths exist
- User runs `docker compose pull` to download images
- User runs `docker compose config` to verify configuration

## Post-Implementation Verification

After implementation, user should run:

1. **Validate configuration:**
   ```bash
   docker compose config
   ```

2. **Download all images:**
   ```bash
   docker compose pull
   ```

3. **Verify images downloaded:**
   ```bash
   docker images
   ```

4. **Check service definitions:**
   ```bash
   docker compose ps
   ```

## Critical Files Summary

1. `C:\Users\nkema\Desktop\itlds\mvp\docker-compose.yml` - Main orchestration (14 services, 5 networks, 11 volumes)
2. `C:\Users\nkema\Desktop\itlds\mvp\.env.example` - Environment variables template
3. `C:\Users\nkema\Desktop\itlds\mvp\PKaKey\Dockerfile` - PKaKey base image definition
4. `C:\Users\nkema\Desktop\itlds\mvp\README.md` - Setup and usage documentation

## Future Implementation Notes

**Phase 2 (after image download):**
- Implement full Django/Wagtail application in PKaKey/Dockerfile
- Add PostgreSQL initialization scripts
- Configure Traefik static configuration
- Export Keycloak realm configuration
- Implement Celery tasks and workflows
- Add PostgREST schema initialization
- Configure pgBouncer connection pooling
- Set up ForwardAuth middleware in Traefik

**Phase 3 (production hardening):**
- Enable TLS/HTTPS in Traefik
- Move secrets to Docker secrets
- Enable Keycloak production mode
- Implement health check endpoints
- Add monitoring (Prometheus/Grafana)
- Set up automated backups
- Configure CI/CD pipeline
