# KoolFlows Microservice

## Overview

KoolFlows is a reverse-proxy and security microservice that combines **Traefik v3.2** (HTTP router) and **CrowdSec** (threat detection and prevention) to provide intelligent traffic routing and DDoS/attack protection for all backend services.

## Architecture

```
┌──────────────────────────────────────┐
│      External Traffic (Port 80)      │
└────────────────┬─────────────────────┘
                 │
         ┌───────▼────────┐
         │    Traefik     │
         │   (Rev Proxy)  │
         │  Dashboard: 8888
         └────────┬───────┘
                  │
      ┌───────────┴───────────┐
      │                       │
┌─────▼──────────────┐  ┌────▼──────────┐
│  CrowdSec Bouncer  │  │Backend Services│
│  (Plugin Middleware)│  │   (Docker)    │
└─────────┬──────────┘  └───────────────┘
          │
    ┌─────▼──────────────────┐
    │   CrowdSec Engine      │
    │  (Local API @ 8080)    │
    │  (AppSec @ 7422)       │
    └────────────────────────┘
```

## Services

### 1. Traefik (traefik:v3.2)

**Purpose**: HTTP reverse proxy and traffic router

**Configuration**:
- **Static Config**: `./traefik/traefik.yml`
  - Entry point: Port 80 (HTTP)
  - Dashboard: Port 8080 (insecure for MVP)
  - Docker provider for automatic service discovery
  - File provider for dynamic configuration
  - Access logging for CrowdSec integration

- **Dynamic Config**: `./traefik/dynamic/config.yml`
  - CrowdSec bouncer plugin middleware configuration
  - Trusted IP ranges for private networks
  - Health check endpoint
  - Dashboard routing

- **Plugins**: `./traefik/plugins-local/`
  - Local CrowdSec bouncer plugin (no remote download required)
  - Properly structured for Traefik's local plugin discovery

**Port Mappings**:
- `80:80` - HTTP incoming traffic
- `443:443` - HTTPS (configured for future use)
- `8888:8080` - Traefik dashboard (mapped to 8888 to avoid conflict with CrowdSec API)

**Environment**:
- Docker socket access for service discovery
- `CROWDSEC_BOUNCER_KEY` - API key for Traefik to authenticate with CrowdSec (set by setup.sh)
- Mount Traefik logs to shared volume for CrowdSec parsing

**Health Check**:
- `traefik healthcheck --ping` every 10s
- Timeout: 5s, Retries: 5

**Routing Labels** (auto-applied to services):
```yaml
traefik.enable=true
traefik.http.routers.<service>.rule=Host(`<subdomain>.theddt.local`)
traefik.http.routers.<service>.entrypoints=web
traefik.http.services.<service>.loadbalancer.server.port=<port>
```

### 2. CrowdSec Engine (crowdsecurity/crowdsec:latest)

**Purpose**: Threat detection, DDoS protection, and decision making (LOCAL-ONLY mode)

**Custom Dockerfile**:
- Copies custom configurations
- Uses custom entrypoint for initialization
- Disables cloud API connectivity due to ISP firewall restrictions

**Custom Entrypoint** (`crowdsec/entrypoint.sh`):
- Disables CrowdSec Cloud API to prevent 403 errors
- Initializes collections for threat detection
- Registers bouncer with CrowdSec
- Supports local-only threat detection mode

**Configuration Files**:
- `./crowdsec/config/acquis.yaml` - Parses system logs and Traefik access logs (JSON format)
- `./crowdsec/config/profiles.yaml` - Decision profiles for threat responses
- `./crowdsec/config/appsec.yaml` - AppSec/WAF configuration (optional)

**Initialization**:
- Installs collections:
  - `crowdsecurity/traefik` - HTTP log parsing
  - `crowdsecurity/http-cve` - HTTP CVE detection
- Generates bouncer API key on first run
- Saves key to shared data volume

**Health Check**:
- `cscli version` every 20s
- Start period: 30s (allows initialization)
- Timeout: 5s, Retries: 5

**Volumes**:
- `crowdsec_data:/var/lib/crowdsec/data` - Persistent CrowdSec state
- `./crowdsec/config/acquis.yaml` - Log acquisition config (read-only)
- `traefik_logs:/var/log/traefik` - Traefik logs (read-only)

**Useful Commands**:
```bash
# List installed collections
docker exec koolflows-crowdsec cscli collections list

# View active decisions (bans)
docker exec koolflows-crowdsec cscli decisions list

# View metrics
docker exec koolflows-crowdsec cscli metrics

# Check for alerts
docker exec koolflows-crowdsec cscli alerts list

# Remove a ban
docker exec koolflows-crowdsec cscli decisions delete --ip <IP_ADDRESS>
```

### 3. CrowdSec Bouncer Plugin (Local)

**Purpose**: Enforce CrowdSec decisions directly in Traefik middleware pipeline

**Implementation**:
- Uses CrowdSec bouncer plugin as a middleware component
- Located at: `./traefik/plugins-local/src/github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin/`
- No separate service required (integrated directly into Traefik)

**Authentication**:
- Uses API key from `CROWDSEC_BOUNCER_KEY` environment variable (set by setup.sh)
- Authenticates with local CrowdSec API on port 8080
- Supports both live and stream modes (currently: live mode)

**Plugin Middleware Configuration** (in `dynamic/config.yml`):
```yaml
http:
  middlewares:
    crowdsec-bouncer:
      plugin:
        bouncer:
          enabled: true
          crowdsecMode: live
          crowdsecLapiHost: crowdsec:8080
          crowdsecLapiKey: ${CROWDSEC_BOUNCER_KEY}
          forwardedHeadersTrustedIPs:
            - 10.0.0.0/8
            - 172.16.0.0/12
            - 192.168.0.0/16
```

**Request Flow**:
1. Request arrives at Traefik (port 80)
2. Traefik applies bouncer middleware
3. Middleware queries CrowdSec local API
4. CrowdSec returns decision (allow/deny)
5. Denied requests return 403 Forbidden
6. Allowed requests proceed to backend service

## Key Features

### Security by Default
- All traffic flows through Traefik
- CrowdSec analyzes access logs in real-time
- Automatic IP bans for suspicious activity (4 hours default)
- Protects all downstream services

### Attack Detection
- HTTP-based attacks (CVE scanning)
- Brute force detection
- Pattern-based threat detection
- Custom scenarios support

### Traffic Management
- Service discovery via Docker labels
- Dynamic route configuration
- Load balancing
- Health monitoring

## Access URLs

- **Traefik Dashboard**: http://traefik.theddt.local (routes through port 8888)
- **Health Check**: http://health.theddt.local
- **CrowdSec API**: http://localhost:8080 (internal only, localhost access)
- **CrowdSec AppSec**: http://localhost:7422 (internal only, localhost access)

## Decision Profiles

### Default IP Remediation (4-hour ban)
- Triggered when CrowdSec detects suspicious activity
- Applies to any IP flagged for remediation

### SSH Brute Force (24-hour ban)
- Detects SSH authentication attempts
- Applies if configured collections enabled

### HTTP Attacks (6-hour ban)
- CVE scanning and HTTP-specific attacks
- Automatic response to malicious payloads

## Adding New Services

To route a new service through KoolFlows:

```yaml
services:
  myservice:
    # ... service config ...
    networks:
      - web
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myservice.rule=Host(`myservice.theddt.local`)"
      - "traefik.http.routers.myservice.entrypoints=web"
      - "traefik.http.services.myservice.loadbalancer.server.port=3000"
```

Then add DNS entry to `/etc/hosts`:
```
127.0.0.1 myservice.theddt.local
```

## Monitoring & Debugging

### View Live Logs
```bash
docker compose logs -f traefik
docker compose logs -f crowdsec
docker compose logs -f  # All services
```

### Check Service Health
```bash
docker compose ps
docker inspect koolflows-traefik
docker inspect koolflows-crowdsec
```

### Test Bouncer Functionality
```bash
# Generate suspicious traffic (e.g., many 404 requests)
for i in {1..20}; do curl http://traefik.theddt.local/nonexistent; done

# Check if IP was banned
docker exec koolflows-crowdsec cscli decisions list

# Verify bouncer blocks the IP
curl http://traefik.theddt.local  # Should get 403 Forbidden
```

## Production Considerations

### Security Hardening
- Enable HTTPS/TLS with Let's Encrypt
- Enable authentication for Traefik dashboard
- Run CrowdSec in production mode
- Enable metrics and monitoring

### Performance
- Add more CrowdSec instances behind a load balancer
- Implement rate limiting in Traefik
- Add caching layer for static content
- Monitor CrowdSec decisions throughput

### High Availability
- Run Traefik in HA mode with multiple replicas
- Use external volume for CrowdSec data
- Implement distributed decision storage
- Set up alerting for CrowdSec decisions

## Troubleshooting

### Services Not Accessible
- Check that services have correct Docker labels
- Verify services are on `web` network
- Check Traefik logs: `docker compose logs traefik`
- Verify DNS entries in `/etc/hosts`

### CrowdSec Not Detecting Threats
- Verify acquis.yaml is correctly configured
- Check that Traefik access logs are being written
- Verify collections are installed: `docker exec koolflows-crowdsec cscli collections list`
- Check CrowdSec logs: `docker compose logs crowdsec`

### Bouncer Plugin Not Working
- Verify bouncer key is set: `grep CROWDSEC_BOUNCER_KEY .env`
- Check bouncer plugin loads: `docker logs koolflows-traefik | grep -i plugin`
- Verify CrowdSec is healthy: `docker compose ps | grep crowdsec`
- Check Traefik middleware config: `docker logs koolflows-traefik | grep -i bouncer`

### 403 Errors from CrowdSec API
- **Expected in local-only mode** - CrowdSec cannot reach cloud API due to firewall
- This is normal and does NOT affect local threat detection
- For details, see `TROUBLESHOOTING.md` and `SETUP_COMPLETE.md` in this directory
- To enable cloud connectivity, ISP firewall must whitelist `api.crowdsec.net` and `hub-data.crowdsec.net`

## Environment Variables

**Auto-generated by setup.sh** (`.env` file):
- `CROWDSEC_BOUNCER_KEY` - API key for Traefik to authenticate with CrowdSec
  - Automatically generated as a secure random key
  - Used by Traefik to communicate with local CrowdSec API
  - Do not commit `.env` file to version control!

**Configuration Files**:
- Traefik static config: `traefik.yml`
- Traefik dynamic config: `dynamic/config.yml` (uses `${CROWDSEC_BOUNCER_KEY}` variable)
- CrowdSec acquisition: `crowdsec/config/acquis.yaml`
- CrowdSec profiles: `crowdsec/config/profiles.yaml`

## Further Information

- **Traefik Documentation**: https://doc.traefik.io/traefik/
- **CrowdSec Documentation**: https://docs.crowdsec.net/
- **Traefik CrowdSec Bouncer**: https://github.com/fbonalair/traefik-crowdsec-bouncer
