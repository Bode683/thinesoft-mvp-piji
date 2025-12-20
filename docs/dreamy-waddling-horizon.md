# MVP Architecture Review & Implementation Plan

## Executive Summary

**Status:** ⚠️ Needs clarification before implementation

Your proposed MVP architecture is **significantly different** from the PKaKey functional specification found in `docs/PKaKey.md`. Before implementing, we need to clarify which direction to pursue.

---

## Architecture Comparison

### Your Proposed MVP
- Traefik (reverse proxy)
- PostgreSQL (database)
- pgAdmin (DB management)
- **PostgREST (auto-generated REST API)**
- pgBouncer (connection pooling)
- Django CMS (future addition)

### Documented Architecture (PKaKey.md)
- Traefik (reverse proxy with TLS/mTLS)
- **Django REST API (custom business logic)**
- Wagtail CMS (operator back-office)
- ViewFlow (workflow engine)
- PostgreSQL + Redis
- Keycloak (authentication/RBAC)
- OCSP Responder + SCEP Proxy + FreeRADIUS
- Monitoring (Prometheus/Grafana)

**Key Difference:** PostgREST (auto-generated, DB-driven API) vs. Django REST Framework (custom, code-driven API with complex PKI business logic)

---

## Critical Questions

### 1. **Project Scope & Intent**
   - Are you building the **PKaKey PKI platform** described in the documentation?
   - OR are you building a **different, simpler application** that happens to use similar technology?
   - If PKaKey: PostgREST likely **cannot** handle the complex PKI logic (CSR validation, certificate signing, SCEP protocol, workflow orchestration)

### 2. **PostgREST vs Django Decision**
   - **PostgREST** is ideal for CRUD operations and simple queries but struggles with:
     - Complex business logic (CSR validation, cryptographic operations)
     - Multi-step workflows (health checks, key rotation)
     - Protocol implementations (SCEP enrollment)
     - File handling (PEM/PKCS#7 certificate formats)
   - **Django** provides full control for complex domain logic but requires more development effort
   - Do you want to start with PostgREST and migrate to Django later, or start with Django from day one?

### 3. **MVP Feature Scope**
   - Which features from the PKaKey spec are in scope for MVP?
   - Or is this a completely different application with different requirements?

---

## Architectural Issues & Recommendations

### ✅ **Good Decisions**

1. **Docker Compose for local development** - Excellent choice for rapid iteration
2. **Traefik as reverse proxy** - Flexible, auto-discovery, good for microservices
3. **Single Docker network** - Simplifies inter-service communication
4. **Hostname-based routing** - Clean separation of concerns
5. **Planning for RLS and DB roles** - Security-first mindset

### ⚠️ **Issues Identified**

#### 1. **pgBouncer: Premature Optimization**
**Problem:** For an MVP with low traffic, pgBouncer adds complexity with minimal benefit.

**Details:**
- PostgREST connection pooling is typically sufficient for early-stage apps
- pgBouncer shines under high concurrent load (100s-1000s of connections)
- Configuration complexity: pooling modes can break certain SQL features
- Adds another service to manage and debug

**Recommendation:** Remove pgBouncer from MVP. Add it later when you have measurable connection pooling issues.

**When to add it back:**
- Database showing "too many connections" errors
- Connection storm scenarios (sudden traffic spikes)
- Multiple services competing for DB connections

---

#### 2. **pgAdmin: Not Essential for MVP**
**Problem:** Adds overhead; CLI tools or lightweight alternatives suffice for early development.

**Details:**
- pgAdmin is heavy (Node.js + Python backend)
- Requires credential management and Traefik routing
- CLI tools (`psql`, `pg_dump`) often faster for dev workflows
- Can add security surface area if misconfigured

**Recommendation:** Remove pgAdmin from initial MVP. Use `psql` via `docker exec` for DB management.

**Alternatives:**
- `docker exec -it postgres psql -U <user> -d <database>` (zero overhead)
- DBeaver or TablePlus on host machine (if GUI needed)
- Add pgAdmin later if multiple team members need web-based access

---

#### 3. **PostgREST + Django CMS: Redundant API Layers**
**Problem:** Two different API paradigms create confusion about where to put logic.

**Details:**
- PostgREST = DB-driven, auto-generated, RESTful CRUD
- Django CMS + DRF = Code-driven, custom business logic APIs
- When you have both, engineers constantly ask: "Which one do I use?"
- Maintenance burden: two routing configs, two auth systems, two API documentation sources

**Recommendation:** Pick ONE primary API strategy:

**Option A: PostgREST-Only (Simple Apps)**
- ✅ Use if: CRUD operations, simple queries, rapid prototyping
- ❌ Avoid if: Complex workflows, cryptographic operations, multi-step processes
- Best for: Admin panels, internal tools, simple data APIs

**Option B: Django-Only (Complex Apps like PKaKey)**
- ✅ Use if: Complex business logic, custom protocols, workflow orchestration
- ❌ Avoid if: Only need basic CRUD and want to avoid writing code
- Best for: PKI platforms, e-commerce, any domain with complex rules

**Option C: Hybrid (Advanced, Not Recommended for MVP)**
- PostgREST for read-heavy, simple endpoints (e.g., listing certificates)
- Django for write-heavy, complex operations (e.g., SCEP enrollment, revocation)
- Requires careful boundaries and documentation

---

#### 4. **Authentication Gap: No JWT Issuer**
**Problem:** You mention JWT validation in PostgREST but don't specify where JWTs are issued.

**Details:**
- PostgREST validates JWTs (checks signature, expiry, claims)
- PostgREST does NOT issue JWTs (no login endpoint, no user/password handling)
- You need a separate authentication service

**Missing Component:** Identity Provider (IdP)

**Solutions:**
- **Keycloak** (mentioned in PKaKey docs) - Full-featured OIDC/SAML provider
- **Django + SimpleJWT** - If using Django, handle auth there
- **Supabase Auth** - If using PostgREST, consider Supabase pattern
- **Auth0/Clerk** - Managed auth services (not self-hosted)

**Recommendation for MVP:**
- If PostgREST path: Add minimal auth service (Django with SimpleJWT, or use Keycloak)
- If Django path: Django handles auth + JWT issuance natively

---

#### 5. **OpenAPI Mode: Security Misconfiguration Risk**
**Problem:** Using `ignore-privileges` in development can hide privilege bugs until production.

**Details:**
- `openapi-mode=ignore-privileges` exposes all DB objects in OpenAPI spec, regardless of user permissions
- Switching to `follow-privileges` in production may break clients expecting endpoints that disappear
- Better to develop with production-like security from the start

**Recommendation:** Use `follow-privileges` from day one, even in dev.

**Alternative:** Keep `ignore-privileges` but add a CI test that generates OpenAPI in both modes and diffs them before each release.

---

#### 6. **Schema Management: No Migration Strategy**
**Problem:** No mention of how DB schema changes are versioned and deployed.

**Details:**
- PostgreSQL init SQL runs once on first container start
- Subsequent schema changes require manual SQL or migration tools
- Without migrations, team members and environments drift out of sync

**Recommendation:** Add a migration tool:

**Option A: Flyway (SQL-based, simple)**
```yaml
flyway:
  image: flyway/flyway
  command: migrate
  volumes:
    - ./migrations:/flyway/sql
  environment:
    - FLYWAY_URL=jdbc:postgresql://postgres:5432/dbname
    - FLYWAY_USER=...
    - FLYWAY_PASSWORD=...
```

**Option B: Django Migrations (if using Django)**
- Built-in, powerful, Python-based
- Automatic conflict detection

**Option C: Alembic (Python, SQLAlchemy-based)**
- Lightweight, flexible
- Good middle ground

---

#### 7. **Secrets Management: Vague Plan**
**Problem:** "Store secrets in environment files or Docker secrets" is not specific enough.

**Details:**
- `.env` files are often accidentally committed to git
- Docker secrets only work in Swarm mode, not Compose (Compose uses `secrets` for bind-mounted files)
- Environment variables visible in `docker inspect`

**Recommendation for MVP:**
1. Create `.env.example` with placeholder values (commit this)
2. Create `.env` with real secrets (add to `.gitignore`)
3. Use `env_file: .env` in docker-compose.yml
4. Document secret generation in README

**For Production:**
- Vault / AWS Secrets Manager / Azure Key Vault
- Kubernetes Secrets with encryption at rest

---

#### 8. **Local DNS: Manual Setup Friction**
**Problem:** Requiring `/etc/hosts` edits is error-prone and OS-specific.

**Details:**
- Windows: `C:\Windows\System32\drivers\etc\hosts` (requires admin)
- macOS/Linux: `/etc/hosts` (requires sudo)
- Easy to forget when onboarding new developers
- Not portable across environments

**Recommendation:**
1. Keep `/etc/hosts` approach for MVP (document clearly)
2. Add a setup script: `scripts/setup-local-dns.sh` (auto-edits hosts file)
3. For production: Use real DNS

**Alternative (Advanced):** Run local DNS server in Docker (dnsmasq) - more complex but automatic

---

#### 9. **Missing: Frontend/Client Application**
**Problem:** Architecture focuses on backend services but no mention of how users/clients interact.

**Details:**
- Who consumes the PostgREST API?
- Is there a web UI? Mobile app? CLI tool?
- For a PKI system, who initiates SCEP enrollment?

**Recommendation:** Clarify client architecture:
- Web UI (React/Vue/Svelte)?
- CLI tool for certificate operations?
- Automated device enrollment (IoT, mobile devices)?

---

#### 10. **Missing: Backup & Disaster Recovery**
**Problem:** No mention of database backups or disaster recovery.

**Details:**
- `./postgres-data` volume persists data, but:
  - Accidental `docker compose down -v` deletes everything
  - No point-in-time recovery (PITR)
  - No off-machine backups

**Recommendation for MVP:**
1. Add pg_dump cron job or backup service
2. Document restore procedure
3. Consider Volume snapshots (Docker volume backup tool)

**For Production:**
- Continuous archiving with WAL shipping
- Cross-region replication

---

### ⚙️ **Architectural Trade-Offs**

| **Aspect** | **Your MVP (PostgREST)** | **PKaKey Spec (Django)** |
|---|---|---|
| **Development Speed** | ⚡ Very fast (auto-generated API) | 🐢 Slower (code every endpoint) |
| **Business Logic Complexity** | ❌ Limited (SQL functions only) | ✅ Unlimited (Python code) |
| **Type Safety** | ⚠️ SQL-driven, runtime errors | ✅ Python type hints, compile-time checks |
| **Protocol Support** | ❌ No SCEP/OCSP built-in | ✅ Can implement any protocol |
| **Workflow Engine** | ❌ Not supported | ✅ ViewFlow integration |
| **Learning Curve** | 📚 Must learn PostgREST config | 📚 Must learn Django patterns |
| **Scalability** | ✅ Excellent for reads | ✅ Excellent for complex operations |
| **API Consistency** | ✅ Auto-consistent with DB schema | ⚠️ Requires discipline to maintain |

---

## Recommended MVP Approaches

### **Approach 1: Simple PostgREST MVP (Generic CRUD App)**
**Best if:** You're NOT building PKaKey; you're building a simple data-driven app with minimal business logic.

**Stack:**
- Traefik
- PostgreSQL
- PostgREST
- ~~pgAdmin~~ (remove, use psql)
- ~~pgBouncer~~ (remove, add later if needed)
- Auth service (Keycloak OR Django auth microservice)

**Pros:** Fastest time-to-first-API, minimal code
**Cons:** Limited to CRUD operations, hard to extend with complex logic

---

### **Approach 2: Django-Based PKaKey MVP (Per Specification)**
**Best if:** You're building the PKaKey PKI platform described in `docs/PKaKey.md`.

**Stack:**
- Traefik
- PostgreSQL
- Redis
- Django REST API (PkaKey app)
- Keycloak (or Django auth for MVP)
- ~~pgAdmin~~ (remove, use psql)
- ~~pgBouncer~~ (remove, add later)
- ~~PostgREST~~ (remove, not needed with Django)

**Pros:** Full control, can implement all PKaKey features
**Cons:** More development effort upfront

---

### **Approach 3: Hybrid (Not Recommended for MVP)**
- PostgREST for read-only queries (certificate listings)
- Django for complex operations (enrollment, revocation, workflows)
- Requires clear API boundaries and dual auth config

**Pros:** Leverage strengths of both
**Cons:** Complexity, cognitive overhead, dual maintenance

---

## Next Steps

Before I can create an implementation plan, I need answers to these questions:

1. **Which project are you building?**
   - [ ] PKaKey PKI platform (per docs/PKaKey.md)
   - [ ] A different, simpler application
   - [ ] PKaKey, but starting with a simplified prototype

2. **Which API approach do you prefer?**
   - [ ] PostgREST (auto-generated, DB-driven)
   - [ ] Django REST Framework (custom, code-driven)
   - [ ] Not sure - need recommendation based on features

3. **What are your MVP features?** (if PKaKey)
   - [ ] Only certificate CRUD (list, create, read)
   - [ ] Include SCEP enrollment
   - [ ] Include revocation + OCSP status
   - [ ] Include workflows (health check, key rotation)
   - [ ] Full spec from docs/PKaKey.md

4. **Authentication priority?**
   - [ ] Can start with no auth (localhost only)
   - [ ] Need basic JWT auth from day one
   - [ ] Need full Keycloak RBAC from day one

5. **Client/Frontend?**
   - [ ] API only (no UI needed yet)
   - [ ] Need web-based admin UI
   - [ ] Need both API and UI

---

## Files to Create (Once Questions Answered)

### Minimal MVP (Either Approach)
```
mvp/
├── docker-compose.yml          # Main orchestration file
├── .env.example                # Secret placeholders
├── .gitignore                  # Ignore .env, volumes, etc.
├── traefik/
│   └── traefik.yml             # Static config
├── postgres/
│   └── init.sql                # Schema + roles setup
└── README.md                   # Setup instructions
```

### PostgREST Approach (Additional)
```
├── postgrest/
│   └── config.conf             # PostgREST configuration
└── auth-service/               # Minimal JWT issuer
    ├── Dockerfile
    └── main.py
```

### Django Approach (Additional)
```
├── pkakey/                     # Django project
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── pkakey/                 # Project settings
│   └── api/                    # DRF app
└── scripts/
    └── wait-for-postgres.sh
```

---

## Estimated Complexity

| **Approach** | **Initial Setup** | **Feature Development** | **Maintenance** |
|---|---|---|---|
| PostgREST MVP | 🟢 4-6 hours | 🟡 Medium (SQL functions) | 🟢 Low (if simple CRUD) |
| Django MVP | 🟡 8-12 hours | 🟢 Easy (Python code) | 🟡 Medium (more code) |
| Full PKaKey (Django) | 🔴 2-3 days | 🟡 Medium-High | 🔴 High (complex domain) |

---

---

## FINAL RECOMMENDATION: Hybrid Architecture for MVP

After analyzing your microservices architecture where:
- **PeSquel** = Shared database layer (PostgreSQL + PostgREST REST API)
- **PKaKey** = PKI microservice consuming PeSquel's API
- **Future services** = Additional microservices using PeSquel

### Architecture Decision

**For MVP, use a HYBRID approach:**

1. **PKaKey → PostgreSQL**: Direct database connection (not via PostgREST)
   - **Reason:** OCSP/SCEP protocols require <100ms latency
   - **Reason:** Complex multi-table transactions for certificate lifecycle
   - **Reason:** Django ORM provides better transaction control

2. **PostgREST**: Ready for future read-only services
   - **Reason:** Perfect for services that need simple CRUD operations
   - **Reason:** Auto-generated API reduces development time for new services
   - **Reason:** Can expose read-only views of certificate data

3. **Shared PostgreSQL Instance**: Single database server, separate databases
   - Databases: `pkakey`, `keycloak`
   - Adequate for MVP traffic
   - Simpler infrastructure management

### What to Include in MVP

**✅ INCLUDE:**
- Traefik (reverse proxy)
- PostgreSQL 16 (single instance, multiple databases)
- PostgREST 12+ (for future services)
- **pgAdmin 4** (critical for development - schema debugging, query analysis)
- Keycloak 23+ (OIDC authentication + RBAC)
- Redis 7+ (Celery broker + OCSP caching)
- Django 5.0+ with DRF (PKaKey application)
- Wagtail 6.0+ (back-office UI)
- ViewFlow (workflow orchestration)
- Celery (async task processing)

**❌ EXCLUDE (add later when needed):**
- pgBouncer (not needed for 1-2 services)
- Prometheus/Grafana (post-MVP observability)
- FreeRADIUS (separate integration project)
- HSM/Vault (use file-based keys for MVP)

---

## Implementation Plan

### Directory Structure

```
C:/Users/nkema/Desktop/itlds/mvp/
├── docker-compose.yml                 # Main orchestration
├── .env.example                       # Environment template
├── .env                               # Secrets (gitignored)
├── .gitignore
├── README.md
│
├── traefik/
│   ├── traefik.yml                    # Static config
│   ├── dynamic/
│   │   └── tls.yml                    # TLS routing
│   └── certs/
│       ├── theddt.local.crt           # Wildcard cert
│       └── theddt.local.key
│
├── PeSquel/
│   ├── README.md
│   ├── postgres/
│   │   ├── init/
│   │   │   ├── 01-create-databases.sql      # pkakey, keycloak DBs
│   │   │   ├── 02-create-roles.sql          # postgrest_anon, authenticator
│   │   │   ├── 03-pkakey-schema.sql         # Initial PKaKey schema
│   │   │   └── 04-postgrest-permissions.sql # PostgREST grants
│   │   └── pgdata/                          # Volume (gitignored)
│   │
│   ├── postgrest/
│   │   └── postgrest.conf             # PostgREST config
│   │
│   └── pgadmin/
│       └── servers.json               # Pre-configured connections
│
├── PKaKey/
│   ├── Dockerfile
│   ├── requirements.txt               # Python dependencies
│   ├── docker-entrypoint.sh           # Startup script
│   ├── .dockerignore
│   │
│   ├── pkakey/                        # Django project
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   └── dev.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── celery.py
│   │
│   ├── apps/
│   │   ├── pki/                       # PKI core
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services/
│   │   │   │   ├── crypto_engine.py
│   │   │   │   ├── certificate_service.py
│   │   │   │   ├── scep_service.py
│   │   │   │   └── ocsp_service.py
│   │   │   └── tasks.py               # Celery tasks
│   │   │
│   │   ├── workflows/                 # ViewFlow
│   │   │   ├── models.py
│   │   │   └── flows.py
│   │   │
│   │   ├── backoffice/                # Wagtail CMS
│   │   │   └── models.py
│   │   │
│   │   └── authentication/            # Keycloak integration
│   │       ├── backends.py            # OIDC backend
│   │       └── middleware.py          # JWT validation
│   │
│   ├── data/
│   │   └── ca/                        # CA certs/keys (volume)
│   │       ├── root_ca.crt
│   │       ├── root_ca.key
│   │       ├── intermediate_ca.crt
│   │       └── intermediate_ca.key
│   │
│   └── tests/
│       ├── conftest.py
│       └── test_pki/
│
├── keycloak/
│   └── realm-export.json              # PKaKey realm config
│
└── docs/
    ├── PKaKey.md                      # Existing spec
    └── architecture.md                # Architecture decisions
```

---

## Critical Files to Create

### Phase 1: Infrastructure (Create First)

| Priority | File | Purpose |
|----------|------|---------|
| 🔴 CRITICAL | `docker-compose.yml` | Orchestrates all services, networks, volumes |
| 🔴 CRITICAL | `.env.example` | Environment variable template |
| 🔴 CRITICAL | `PeSquel/postgres/init/01-create-databases.sql` | Create pkakey & keycloak databases |
| 🔴 CRITICAL | `PeSquel/postgres/init/02-create-roles.sql` | PostgreSQL roles for PostgREST |
| 🔴 CRITICAL | `PeSquel/postgres/init/03-pkakey-schema.sql` | Initial PKaKey schema |
| 🟡 HIGH | `traefik/traefik.yml` | Traefik static configuration |
| 🟡 HIGH | `PeSquel/postgrest/postgrest.conf` | PostgREST configuration |
| 🟢 MEDIUM | `PeSquel/pgadmin/servers.json` | pgAdmin server connections |

### Phase 2: PKaKey Foundation

| Priority | File | Purpose |
|----------|------|---------|
| 🔴 CRITICAL | `PKaKey/Dockerfile` | Django container |
| 🔴 CRITICAL | `PKaKey/requirements.txt` | Python dependencies |
| 🔴 CRITICAL | `PKaKey/docker-entrypoint.sh` | Startup script (migrations) |
| 🔴 CRITICAL | `PKaKey/pkakey/settings/base.py` | Django settings |
| 🔴 CRITICAL | `PKaKey/pkakey/settings/dev.py` | Dev environment overrides |
| 🟡 HIGH | `PKaKey/pkakey/urls.py` | URL routing |
| 🟡 HIGH | `PKaKey/pkakey/celery.py` | Celery configuration |

### Phase 3: PKI Core

| Priority | File | Purpose |
|----------|------|---------|
| 🔴 CRITICAL | `PKaKey/apps/pki/models.py` | CertificateRecord model |
| 🔴 CRITICAL | `PKaKey/apps/pki/services/crypto_engine.py` | CSR validation, signing |
| 🔴 CRITICAL | `PKaKey/apps/pki/services/certificate_service.py` | Cert lifecycle logic |
| 🟡 HIGH | `PKaKey/apps/pki/serializers.py` | DRF serializers |
| 🟡 HIGH | `PKaKey/apps/pki/views.py` | DRF viewsets |
| 🟡 HIGH | `PKaKey/apps/pki/services/scep_service.py` | SCEP protocol |
| 🟡 HIGH | `PKaKey/apps/pki/services/ocsp_service.py` | OCSP responder |

### Phase 4: Authentication

| Priority | File | Purpose |
|----------|------|---------|
| 🔴 CRITICAL | `PKaKey/apps/authentication/middleware.py` | JWT validation |
| 🔴 CRITICAL | `PKaKey/apps/authentication/backends.py` | OIDC auth backend |
| 🟡 HIGH | `keycloak/realm-export.json` | Keycloak realm config |

---

## Schema Migration Strategy

### Ownership Model: Django Migrations
- **Initial Setup:** SQL scripts create baseline schema
- **Ongoing Changes:** Django migrations manage schema evolution
- **PostgREST:** Auto-reflects schema changes (restart service)

### Workflow:
1. Developer modifies Django models
2. Run `makemigrations` + `migrate` in PKaKey container
3. Restart PostgREST to reflect new schema
4. Update PostgREST permissions if needed

---

## Authentication Flow

### Three-Layer Architecture

**1. User Authentication (OIDC)**
```
Browser → Traefik → PKaKey → Keycloak
- User logs in via Keycloak
- Django validates OIDC token
- Session created
```

**2. API Authentication (JWT)**
```
API Client → Traefik → PKaKey
- Client obtains JWT from Keycloak
- Includes "Authorization: Bearer <jwt>"
- PKaKey middleware validates JWT
- DRF enforces RBAC via claims
```

**3. Service-to-Service (Future)**
```
Future Service → PostgREST
- Service uses long-lived service account JWT
- PostgREST validates and enforces RLS
```

### Keycloak Configuration
- **Realm:** `pkakey`
- **Client:** `pkakey-backend` (confidential)
- **Roles:** `pki-admin`, `pki-operator`, `pki-viewer`
- **Service Account:** Enabled for future services

---

## Service Communication

### Internal (Docker Network)
- PKaKey → PostgreSQL: `postgres:5432` (direct)
- PKaKey → Keycloak: `http://keycloak:8080`
- PKaKey → Redis: `redis:6379`
- Future → PostgREST: `http://postgrest:3000`

### External (via Traefik)
- `https://theddt.local` → Traefik dashboard
- `https://api.theddt.local` → PostgREST
- `https://pkakey.theddt.local` → PKaKey Django
- `https://pgadmin.theddt.local` → pgAdmin
- `https://auth.theddt.local` → Keycloak

---

## Implementation Order (Sprints)

### Sprint 1: Infrastructure (Days 1-4)
- Create docker-compose.yml with all services
- Configure Traefik with TLS
- Create PostgreSQL init scripts
- Configure PostgREST
- Setup Keycloak realm

**Deliverable:** `docker-compose up` brings up all infrastructure

### Sprint 2: PKaKey Foundation (Days 5-9)
- Create Django project structure
- Configure database connection
- Setup Celery + Redis
- Create basic PKI models
- Add Traefik routing

**Deliverable:** PKaKey API accessible via Traefik

### Sprint 3: Authentication (Days 10-12)
- Configure OIDC backend
- Implement JWT middleware
- Setup DRF permissions
- Test auth flow end-to-end

**Deliverable:** Protected API with RBAC working

### Sprint 4: PKI Core (Days 13-17)
- Implement crypto engine (CSR validation, signing)
- Create certificate service (issue, revoke)
- Build SCEP endpoint
- Build OCSP responder

**Deliverable:** Full certificate lifecycle working

### Sprint 5: Workflows & Backoffice (Days 18-20)
- Create ViewFlow workflows (health check, key rotation)
- Setup Wagtail admin UI
- Write tests
- Document deployment

**Deliverable:** Complete MVP with monitoring workflows

---

## Potential Issues & Mitigations

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Self-signed cert trust | Browser warnings | Use `mkcert` for local dev |
| Keycloak startup dependencies | Circular dependency | Use health checks + wait-for-it script |
| CA key security | PKI compromise | File permissions 600, volume encryption |
| SCEP/OCSP latency | Failed enrollments | Redis caching, DB indexes |
| Windows path issues | Volume mount failures | Use WSL2, relative paths |
| Schema migration conflicts | Concurrent migrations | Migration lock table (Django 4.2+) |

---

## Summary

This architecture provides:
- ✅ Clean separation: PeSquel (data) vs PKaKey (business logic)
- ✅ Future-proof: PostgREST ready for additional microservices
- ✅ Performance: Direct DB access for latency-sensitive PKI operations
- ✅ Security: Keycloak OIDC + JWT + RBAC from day one
- ✅ Scalability: Stateless services, horizontal scaling ready
- ✅ Developer experience: pgAdmin for debugging, Docker Compose for orchestration

**Next Steps:** Begin Phase 1 implementation with docker-compose.yml and infrastructure setup.
