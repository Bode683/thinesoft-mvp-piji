# KoolFlows CrowdSec + Traefik - Setup Complete

**Date Completed**: 2025-12-20
**Status**: ✅ OPERATIONAL IN LOCAL-ONLY MODE

## Overview

The KoolFlows microservice stack is now operational with CrowdSec and Traefik fully integrated in **local-only mode**. Due to ISP firewall restrictions blocking access to CrowdSec Cloud API, the setup has been configured to operate independently without cloud connectivity.

## Current Architecture

```
┌─────────────────────────────────────┐
│      External Traffic (Port 80)     │
└────────────────┬────────────────────┘
                 │
         ┌───────▼────────┐
         │    Traefik     │
         │   (Rev Proxy)  │
         └────────┬───────┘
                  │
     ┌────────────┴────────────┐
     │                         │
┌────▼──────────────┐  ┌──────▼──────────┐
│  CrowdSec Bouncer  │  │ Backend Services│
│  Middleware Plugin │  │    (Docker)     │
└────────┬──────────┘  └─────────────────┘
         │
    ┌────▼──────────────────┐
    │  CrowdSec Engine      │
    │  (Local API @ 8080)   │
    │  (AppSec @ 7422)      │
    └───────────────────────┘
```

## Containers Running

### ✅ Healthy Containers

**CrowdSec** (`koolflows-crowdsec`)
- Status: `Healthy`
- API: `http://localhost:8080` (internal only)
- AppSec: `http://localhost:7422` (internal only)
- Mode: **Local-only (no cloud connectivity)**
- Logs: Monitor with `docker compose logs -f crowdsec`

**Traefik** (`koolflows-traefik`)
- Status: Responding (health check issue due to Docker socket timeout)
- HTTP: `0.0.0.0:80`
- HTTPS: `0.0.0.0:443` (configured for future use)
- Dashboard: `http://localhost:8888` (local access)
- Plugin: `bouncer` (CrowdSec Bouncer - LOADED ✓)
- Logs: Monitor with `docker compose logs -f traefik`

## Configuration Summary

### Environment Variables (`.env`)
```bash
# .env file in project root
CROWDSEC_BOUNCER_KEY=E5vMONM2eNrpEkyJx8yLmAKgMdCQ3x1HfnRDrux2yec
```

### Key Files Modified

1. **traefik.yml** - Static configuration
   - JSON access logs for CrowdSec parsing
   - Local plugin configuration for bouncer
   - Increased Docker client timeout (60s)

2. **dynamic/config.yml** - Dynamic middleware configuration
   - `crowdsec-bouncer` middleware using local bouncer plugin
   - `crowdsec-full` chain middleware for services
   - Trusted IP ranges for private networks

3. **crowdsec/config/acquis.yaml** - Log acquisition
   - Syslog parsing (auth.log, syslog)
   - Traefik access log parsing (JSON format)
   - AppSec listener on port 7422

4. **crowdsec/entrypoint.sh** - Initialization script
   - Disables cloud API on startup
   - Generates bouncer tokens on first run
   - Configures collections for threat detection

5. **docker-compose.yml** - Service orchestration
   - Persistent volume for CrowdSec data (`crowdsec_data`)
   - Proper port mappings and environment variables
   - Health check configuration for both services

## What's Working ✅

- [x] Traefik reverse proxy routing
- [x] CrowdSec bouncer plugin loads in Traefik
- [x] Local CrowdSec API accessible on port 8080
- [x] Log acquisition and parsing (Traefik logs)
- [x] Threat detection (local pattern matching)
- [x] Bouncer API key authentication
- [x] Docker service discovery in Traefik
- [x] Middleware pipeline ready for protection

## Known Limitations ⚠️

Due to ISP firewall blocking `api.crowdsec.net` and `hub-data.crowdsec.net`:

- No cloud threat intelligence sync
- No automatic collection/parser updates
- No watcher enrollment with CrowdSec Console
- No GeoIP database downloads
- **Operating in local-only threat detection mode**

These limitations do **NOT** affect local threat detection capabilities. CrowdSec will still:
- Parse and analyze Traefik access logs
- Detect attacks using pre-installed collection rules
- Block malicious IPs based on local patterns
- Maintain decisions locally

## Monitoring and Health Checks

### Check Service Health
```bash
docker compose ps
```

### View Logs
```bash
# CrowdSec logs
docker compose logs -f crowdsec

# Traefik logs
docker compose logs -f traefik

# Combined
docker compose logs -f crowdsec traefik
```

### CrowdSec Commands
```bash
# List active decisions (banned IPs)
docker exec koolflows-crowdsec cscli decisions list

# View metrics
docker exec koolflows-crowdsec cscli metrics

# List registered bouncers
docker exec koolflows-crowdsec cscli bouncers list

# Check version/health
docker exec koolflows-crowdsec cscli version
```

### Test Traefik
```bash
# Dashboard (redirects, requires Host header)
curl -H "Host: traefik.theddt.local" http://localhost:8888/

# API health
curl http://localhost:8888/api/rawdata

# Test HTTP routing
curl http://localhost/
```

## Next Steps (Optional)

### If ISP Firewall is Lifted

1. **Enable cloud API connectivity**:
   - Whitelist `api.crowdsec.net` and `hub-data.crowdsec.net` in firewall
   - Update `crowdsec/entrypoint.sh` to remove cloud API disabling
   - Rebuild CrowdSec image: `docker compose build --no-cache crowdsec`
   - Restart: `docker compose restart crowdsec`

2. **Enroll with CrowdSec Console**:
   ```bash
   docker exec koolflows-crowdsec cscli console enroll -e context YOUR_ENROLLMENT_CODE
   ```

3. **Verify enrollment**:
   ```bash
   docker logs koolflows-crowdsec | grep -i "enrolled\|success"
   ```

### Add More Services

To route additional services through Traefik+CrowdSec:

1. Add Docker labels to your service:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myservice.rule=Host(`myservice.theddt.local`)"
  - "traefik.http.routers.myservice.entrypoints=web"
  - "traefik.http.routers.myservice.middlewares=crowdsec-bouncer@file"
  - "traefik.http.services.myservice.loadbalancer.server.port=3000"
```

2. Add DNS entry to `/etc/hosts`:
```
127.0.0.1 myservice.theddt.local
```

3. Traefik will automatically discover and route the service through CrowdSec protection

## Testing Threat Detection

### Simulate Suspicious Activity
```bash
# Generate many 404 requests (triggers detection)
for i in {1..20}; do curl http://localhost/nonexistent; done

# Check if IP was banned
docker exec koolflows-crowdsec cscli decisions list

# Verify bouncer blocks the IP
curl http://localhost/  # Should get 403 if blocked
```

### View Alerts
```bash
docker exec koolflows-crowdsec cscli alerts list
```

## Troubleshooting

### CrowdSec won't start
1. Check logs: `docker logs koolflows-crowdsec`
2. If seeing CAPI errors, ensure entrypoint script is disabling cloud API
3. Rebuild image: `docker compose build --no-cache crowdsec`

### Traefik health check failing
1. This is expected due to Docker socket timeout issues
2. Service is still operational despite health check status
3. Test with: `curl -v http://localhost/`

### Bouncer middleware not loading
1. Check plugin loads: `docker logs koolflows-traefik | grep plugin`
2. Verify `CROWDSEC_BOUNCER_KEY` is set in `.env`
3. Ensure plugin path is correct in `traefik.yml`

### No threat detection happening
1. Check logs being written: `docker logs koolflows-traefik | tail -20`
2. Verify acquisition config: `docker exec koolflows-crowdsec cat /etc/crowdsec/acquis.yaml`
3. Check collections installed: `docker exec koolflows-crowdsec cscli collections list`

## Files for Reference

**Documentation**:
- `TROUBLESHOOTING.md` - Detailed troubleshooting and issue analysis
- `SETUP_COMPLETE.md` - This file

**Configuration**:
- `.env` - Environment variables (contains bouncer API key)
- `KoolFlows/traefik/traefik.yml` - Traefik static config
- `KoolFlows/traefik/dynamic/config.yml` - Traefik dynamic config & middleware
- `KoolFlows/crowdsec/config/acquis.yaml` - Log acquisition rules
- `KoolFlows/crowdsec/config/profiles.yaml` - Decision profiles
- `KoolFlows/crowdsec/entrypoint.sh` - CrowdSec initialization script
- `docker-compose.yml` - Service definitions

## Architecture Decisions

**Why Local-Only Mode?**
- ISP firewall blocks outbound HTTPS to CrowdSec infrastructure
- Local threat detection is sufficient for most use cases
- Avoids dependency on external cloud services
- Provides faster decision-making (no cloud roundtrips)

**Why Plugin vs Standalone Bouncer?**
- Direct integration with Traefik middleware pipeline
- Lower latency for decision enforcement
- Simpler deployment (no separate bouncer service)
- Easier credential management

**Why Persistent Volume for CrowdSec Data?**
- Ensures decisions persist across container restarts
- Maintains decision history for audit trails
- Allows incremental learning across sessions
- Prevents data loss on updates

## Version Information

- **Traefik**: v3.6.5
- **CrowdSec**: v1.7.4
- **CrowdSec Bouncer Plugin**: v1.4.7 (local)
- **Docker Compose**: Version 2.x+

## Support & Next Steps

For issues or questions:
1. Check `TROUBLESHOOTING.md` for detailed problem analysis
2. Review container logs: `docker compose logs -f`
3. Check CrowdSec metrics: `docker exec koolflows-crowdsec cscli metrics`
4. Test basic connectivity: `curl http://localhost/`

---

**Status**: Ready for integration with backend services
**Last Updated**: 2025-12-20
**Mode**: Local-Only (No Cloud Connectivity)
