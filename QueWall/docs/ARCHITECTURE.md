# QueWall Architecture Documentation

## Overview

QueWall is a complete authentication infrastructure stack based on industry-standard components:
- **Traefik** - Cloud-native reverse proxy and load balancer
- **Keycloak** - Open-source identity and access management (IAM) solution
- **oauth2-proxy** - Forward authentication proxy for OIDC/OAuth2
- **PostgreSQL** - Relational database backend for Keycloak
- **Docker & Docker Compose** - Container orchestration

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User's Browser                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │       Traefik          │
                  │   (Port 80/8080)       │
                  │   Reverse Proxy &      │
                  │   ForwardAuth Router   │
                  └──────────┬─────────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
      ┌─────────────────────┐  ┌──────────────────┐
      │   oauth2-proxy      │  │  Protected       │
      │   :4180             │  │  Services        │
      │                     │  │  (whoami, etc)   │
      │ OIDC/OAuth2 Client  │  │                  │
      │ ForwardAuth Handler │  │  :80/xxxx        │
      └──────────┬──────────┘  └──────────────────┘
                 │
                 │ OIDC Protocol
                 │ (Discovery, Token, Userinfo)
                 │
                 ▼
      ┌─────────────────────────────┐
      │       Keycloak              │
      │       :8080                 │
      │ OpenID Connect Provider     │
      │ (theddt realm)              │
      │                             │
      │ - User Authentication       │
      │ - User Management           │
      │ - Token Issuance            │
      │ - OIDC Discovery            │
      └──────────┬──────────────────┘
                 │
                 │ PostgreSQL Protocol
                 │ (tcp:5432)
                 │
                 ▼
      ┌─────────────────────────────┐
      │       PostgreSQL             │
      │       :5432                 │
      │ Keycloak Database           │
      │                             │
      │ - Realms                    │
      │ - Users & Groups            │
      │ - Clients & Protocols       │
      │ - Sessions & Tokens         │
      └─────────────────────────────┘
```

## Component Details

### 1. Traefik (Reverse Proxy & Router)

**Role**: Entry point for all user traffic, request routing, and authentication enforcement

**Configuration**:
- Listens on port 80 (HTTP only for MVP)
- Provides ForwardAuth middleware for authentication
- Routes based on Host headers (*.theddt.local)
- No TLS termination (HTTP only)
- Dashboard on port 8080

**Key Features**:
- Dynamic service discovery from Docker labels
- Middleware for cross-cutting concerns
- Built-in health checks
- Request logging

**Service Routing**:
- `keycloak.theddt.local` → Keycloak service (port 8080)
- `auth.theddt.local` → oauth2-proxy service (port 4180)
- `app.theddt.local` → Protected services (port 80)

### 2. oauth2-proxy (OIDC Client & ForwardAuth Handler)

**Role**: OIDC client that handles authentication flows and injects user headers into requests

**OIDC Configuration**:
- **Provider**: OIDC (OpenID Connect)
- **Issuer URL**: `http://keycloak:8080/realms/theddt`
- **Client ID**: `oauth2-proxy-client`
- **Client Type**: Confidential (requires secret)
- **Redirect URI**: `http://auth.theddt.local/oauth2/callback`

**Endpoints**:
- `/oauth2/auth` - ForwardAuth endpoint (called by Traefik)
- `/oauth2/callback` - OAuth2 callback endpoint
- `/oauth2/sign_out` - Logout endpoint
- `/ping` - Health check endpoint

**Session Management**:
- Uses secure httpOnly cookies for session storage
- Cookie domain: `.theddt.local` (shared across subdomains)
- Default session timeout: 300 seconds (configurable)

**Header Injection**:
Forwards authentication claims as HTTP headers:
- `X-Auth-Request-User` - User identifier (email or username)
- `X-Auth-Request-Email` - User email address
- `X-Auth-Request-Preferred-Username` - User's preferred username
- `X-Auth-Request-Groups` - User's group memberships (JSON array)

### 3. Keycloak (OpenID Connect Identity Provider)

**Role**: Centralized identity and access management

**Realm Configuration**:
- **Realm Name**: `theddt`
- **Database**: PostgreSQL (external)
- **Admin Console**: http://keycloak.theddt.local
- **OIDC Discovery**: http://keycloak.theddt.local/realms/theddt/.well-known/openid-configuration

**Configured Client**:
- **Client ID**: `oauth2-proxy-client`
- **Client Type**: Confidential (OAuth2 standard)
- **Authentication Flow**: Authorization Code Flow with PKCE
- **Valid Redirect URIs**: `http://auth.theddt.local/oauth2/callback`
- **Access Type**: Confidential (requires client secret)

**Protocol Mappers**:
1. **Audience Mapper** - Adds `oauth2-proxy-client` to JWT audience
2. **Groups Mapper** - Maps Keycloak groups to OIDC `groups` claim
3. **Email Mapper** - Standard email claim mapping
4. **Preferred Username** - Maps Keycloak username to preferred_username

**Test User**:
- **Username**: `testuser`
- **Email**: `testuser@theddt.local`
- **Password**: `password123`
- **Roles**: default-roles-theddt, offline_access, uma_authorization

**Scopes**:
- `openid` - OIDC scope (required)
- `profile` - User profile information
- `email` - User email address
- `groups` - User group memberships

### 4. PostgreSQL (Database Backend)

**Role**: Persistent storage for Keycloak realm configuration and user data

**Configuration**:
- **Container Name**: `quewall-postgres`
- **Port**: 5432 (internal only, not exposed)
- **Database**: `keycloak`
- **User**: `keycloak`
- **Volume**: `postgres_data` (named volume)

**Stored Data**:
- Realm definitions
- User accounts and credentials
- Roles and groups
- Client configurations
- Sessions and tokens
- Event logs

**Persistence**:
- Data persists across container restarts
- Volume can be backed up independently
- Use `--keep-volumes` flag with teardown.sh to preserve data

## Authentication Flow

### 1. Initial Request (Unauthenticated User)

```
Client → GET http://app.theddt.local/
         │
         ▼
    Traefik ForwardAuth Middleware
         │
         ├─→ Calls oauth2-proxy:/oauth2/auth
         │
         ▼
    oauth2-proxy checks session cookie
         │
         └─→ No valid session found
             │
             ▼
         oauth2-proxy returns 401/302
         └─→ Redirect to Keycloak login
```

### 2. Login (User at Keycloak)

```
Client → Redirected to Keycloak login
         │
         ├─→ GET /auth/realms/theddt/protocol/openid-connect/auth?
         │       client_id=oauth2-proxy-client&
         │       redirect_uri=http://auth.theddt.local/oauth2/callback&
         │       response_type=code&
         │       scope=openid profile email groups&
         │       ...
         │
         ▼
    User enters credentials: testuser / password123
         │
         ▼
    Keycloak validates credentials
         │
         ├─→ Generates authorization code
         └─→ Redirects back to oauth2-proxy callback
```

### 3. Token Exchange (Backend)

```
oauth2-proxy → Keycloak Token Endpoint
              (POST /auth/realms/theddt/protocol/openid-connect/token)
              │
              ├─ Authorization Code
              ├─ Client ID: oauth2-proxy-client
              ├─ Client Secret: [from Docker secret]
              │
              ▼
         Keycloak validates and exchanges code for token
         │
         ▼
         Returns:
         - ID Token (JWT with user claims)
         - Access Token (JWT)
         - Refresh Token (for token refresh)
```

### 4. Session Creation (oauth2-proxy)

```
oauth2-proxy receives tokens
         │
         ├─ Validates token signature against Keycloak JWKS
         ├─ Extracts user claims
         ├─ Creates session with claims
         └─ Sets secure httpOnly cookie with session ID
             (Cookie domain: .theddt.local)
             │
             ▼
         Redirect to original URL: http://app.theddt.local/
```

### 5. Subsequent Requests (Authenticated User)

```
Client → GET http://app.theddt.local/
         (Browser automatically includes session cookie)
         │
         ▼
    Traefik ForwardAuth Middleware
         │
         ├─→ Calls oauth2-proxy:/oauth2/auth
         │
         ▼
    oauth2-proxy validates session cookie
         │
         ├─→ Valid session found
             │
             ├─ Extracts user claims from session
             ├─ Adds headers: X-Auth-Request-User, etc.
             └─ Returns 200 OK with headers
             │
             ▼
         Traefik forwards request to backend service
         with X-Auth-Request-* headers
         │
         ▼
    Protected service receives authenticated request
    (can read user info from headers)
```

## Network Configuration

### Docker Network

**Name**: `quewall-network`
**Driver**: Bridge (user-defined)

**Service DNS Resolution** (internal):
- `postgres` → 172.xx.0.2:5432 (example IP)
- `keycloak` → 172.xx.0.3:8080
- `oauth2-proxy` → 172.xx.0.4:4180
- `whoami` → 172.xx.0.5:80
- `traefik` → 172.xx.0.6:80

**External Access** (via Traefik):
- `keycloak.theddt.local` (port 80 → Traefik → Keycloak:8080)
- `auth.theddt.local` (port 80 → Traefik → oauth2-proxy:4180)
- `app.theddt.local` (port 80 → Traefik → whoami:80)

### Networking Benefits

1. **Service Discovery**: Services communicate via DNS names, not IP addresses
2. **Isolation**: Services only accessible through Traefik (by default)
3. **Simplified Configuration**: No port mapping complexity
4. **Network Policy Ready**: Can add network policies in future

## Data Flow & Security

### Request Headers Through the Stack

```
Browser Request:
  GET http://app.theddt.local/whoami
  Host: app.theddt.local
  Cookie: oauth2proxy_=<session_id>
    │
    ▼
Traefik Receives:
    ├─ Checks route: Host(app.theddt.local) = YES
    ├─ Applies middleware: oauth2-auth
    │
    ├─→ Calls oauth2-proxy:/oauth2/auth
    │   ├─ Validates cookie
    │   └─ Returns 200 with headers:
    │       X-Auth-Request-User: testuser@theddt.local
    │       X-Auth-Request-Email: testuser@theddt.local
    │       X-Auth-Request-Preferred-Username: testuser
    │       X-Auth-Request-Groups: ["default-roles-theddt"]
    │
    ├─ Traefik forwards to backend service:
    │
    ▼
Backend Service (whoami) Receives:
    GET http://app.theddt.local/whoami
    Host: app.theddt.local
    X-Auth-Request-User: testuser@theddt.local
    X-Auth-Request-Email: testuser@theddt.local
    X-Auth-Request-Preferred-Username: testuser
    X-Auth-Request-Groups: ["default-roles-theddt"]
    X-Forwarded-Proto: http
    X-Forwarded-Host: app.theddt.local
    (and other X-Forwarded-* headers)
```

### Secret Management

**Secrets Stored in Docker Secrets** (not environment variables):

1. `keycloak_admin_password`
   - Used for: Keycloak admin console access
   - Location: `/run/secrets/keycloak_admin_password` (inside container)

2. `postgres_password`
   - Used for: PostgreSQL authentication
   - Location: `/run/secrets/postgres_password`
   - Shared between: Keycloak and PostgreSQL

3. `oauth2_client_secret`
   - Used for: OIDC client authentication with Keycloak
   - Location: `/run/secrets/oauth2_client_secret`
   - Also injected into: realm-export.json during setup

4. `oauth2_cookie_secret`
   - Used for: Encrypting session cookies
   - Location: `/run/secrets/oauth2_cookie_secret`
   - Generated as: URL-safe base64, 32 bytes

**Why Docker Secrets?**
- More secure than environment variables (not visible in `docker inspect`)
- Supports secret rotation
- Works with Docker Swarm and Compose
- Secrets mounted as read-only files

## Service Dependencies

```
┌─────────────────────────────────────┐
│         PostgreSQL                  │
│    (must start first)               │
└────────────────────┬────────────────┘
                     │ requires
                     ▼
         ┌─────────────────────────────┐
         │      Keycloak               │
         │   (discovery, tokens)       │
         └──────────────┬──────────────┘
                        │ requires
                        ▼
        ┌────────────────────────────────┐
        │     oauth2-proxy               │
        │   (ForwardAuth handler)        │
        └────────────────────────────────┘
                        │
        ┌───────────────┴──────────────┐
        │                              │
        ▼                              ▼
    ┌─────────┐                  ┌──────────┐
    │ Traefik │◄────────────────►│  whoami  │
    │ (router)│   traffic flow   │ (service)│
    └─────────┘                  └──────────┘
```

**Startup Order** (enforced by setup.sh):
1. PostgreSQL (must be ready before Keycloak)
2. Keycloak (must be ready before oauth2-proxy)
3. oauth2-proxy (must be ready before Traefik routes requests)
4. Traefik & whoami (final services)

## Extensibility

### Adding Protected Services

To protect additional HTTP services with the QueWall authentication stack, simply add them to `docker-compose.yml` with the ForwardAuth middleware:

```yaml
my-service:
  image: my-service:latest
  networks:
    - quewall-network
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.my-service.rule=Host(`my-service.theddt.local`)"
    - "traefik.http.routers.my-service.entrypoints=web"
    - "traefik.http.routers.my-service.middlewares=oauth2-auth"  # Attach auth middleware
    - "traefik.http.services.my-service.loadbalancer.server.port=8000"
```

The service will automatically:
- Require authentication before access
- Receive user info via X-Auth-Request-* headers
- Not need to implement OIDC directly

## Limitations (MVP)

1. **HTTP Only**
   - No TLS/HTTPS
   - No certificate validation
   - Suitable for development/testing only

2. **Session Storage**
   - oauth2-proxy uses in-memory sessions
   - Restarting oauth2-proxy logs out all users
   - No session persistence across instances

3. **Database**
   - Single PostgreSQL instance
   - No replication or failover
   - No automated backups

4. **Keycloak**
   - Development mode (`start-dev`)
   - In-memory cache only
   - No clustering support

5. **Scalability**
   - Single instance of each service
   - No load balancing between replicas

## Production Considerations

For production deployment, consider:

1. **Security**
   - Enable TLS/HTTPS
   - Use certificate authority (Let's Encrypt)
   - Implement network segmentation
   - Add rate limiting

2. **High Availability**
   - Keycloak clustering
   - PostgreSQL replication and failover
   - Multiple oauth2-proxy instances with load balancing
   - Traefik as highly available load balancer

3. **Session Management**
   - Use Redis for session storage (oauth2-proxy)
   - Configure session timeout policies
   - Implement refresh token rotation

4. **Monitoring & Logging**
   - Prometheus metrics
   - ELK stack for centralized logging
   - Distributed tracing
   - Health check monitoring

5. **Identity Management**
   - LDAP/AD integration
   - Custom user provisioning
   - Role-based access control (RBAC)
   - Audit logging

6. **Backup & Recovery**
   - PostgreSQL backup strategy
   - Keycloak configuration versioning
   - Disaster recovery plan

## References

- [Traefik Documentation](https://doc.traefik.io/)
- [OAuth2-Proxy Documentation](https://oauth2-proxy.github.io/oauth2-proxy/)
- [Keycloak Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/)
- [OpenID Connect Specification](https://openid.net/specs/openid-connect-core-1_0.html)
- [Docker Compose Specification](https://docs.docker.com/compose/compose-file/)
