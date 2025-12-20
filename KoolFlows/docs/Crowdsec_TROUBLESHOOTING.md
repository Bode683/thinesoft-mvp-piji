# KoolFlows CrowdSec + Traefik Integration - Troubleshooting Documentation

**Date**: 2025-12-20
**Issue**: CrowdSec and Traefik integration failing with 403 Forbidden errors and container health check failures

## Problem Summary

The KoolFlows microservice (Traefik + CrowdSec) was experiencing:
- CrowdSec containers restarting due to API authentication failures
- 403 Forbidden errors when attempting to authenticate with CrowdSec Cloud API
- Health check failures
- Inability to download GeoIP data and other resources
- Traefik plugin loading errors

## Root Cause Analysis

### Issue 1: Network Connectivity to CrowdSec Cloud API ❌ UNRESOLVED

**Error Messages:**
```
time="2025-12-20T13:15:56Z" level=fatal msg="api server init: unable to run local API:
authenticate watcher (72bb98ce203347fe8aeec80b189ead24OQ3UWKcyNSPi1Db1): API error: Forbidden"

cscli console enroll: could not enroll instance:
Post "https://api.crowdsec.net/v3/watchers/enroll": API error: Forbidden

level=warning msg="Failed to check last modified: bad HTTP code 403 for
https://hub-data.crowdsec.net/mmdb_update/GeoLite2-City.mmdb"
```

**Root Cause**: ISP-level firewall blocking outbound HTTPS connections to CrowdSec infrastructure

**Endpoints Blocked**:
- `api.crowdsec.net` (port 443) - Watcher enrollment and authentication
- `hub-data.crowdsec.net` (port 443) - GeoIP data, parsers, and hub content

**Connectivity Testing Results**:
```bash
# From host machine - WORKS
curl -v https://github.com
# Result: Successfully connected to GitHub (TLS established)

# From host machine - FAILS
curl -v https://api.crowdsec.net
# Result: Connection timeout after 10001 milliseconds
# DNS resolves: 54.194.95.0, 34.250.8.127, 52.215.215.208
# TCP connection times out (firewall blocks)

# From CrowdSec container - FAILS
docker exec koolflows-crowdsec nslookup api.crowdsec.net
# Result: DNS resolution works (54.194.95.0, 34.250.8.127, 52.215.215.208)
# But TCP connection cannot be established
```

**Impact**:
- CrowdSec cannot enroll with CrowdSec Console
- CrowdSec cannot authenticate watchers
- CrowdSec cannot download GeoIP databases and collection updates
- CrowdSec container continuously restarts

### Issue 2: Traefik Plugin Loading with Network Restrictions ✅ RESOLVED

**Original Error**:
```
ERR [1mPlugins are disabled because an error has occurred.[0m [36merror=[0m[31m
"1 error occurred:\n\t* failed to open the plugin manifest
plugins-local/src/github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin/.traefik.yml:
open plugins-local/src/github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin/.traefik.yml:
no such file or directory\n\n"
```

**Root Cause**:
1. Initial attempt used remote plugin download from `plugins.traefik.io`
2. Remote download fails due to network timeout (same ISP firewall blocking)
3. Plugin directory structure was incorrect for local plugin mode

**Solution Implemented**:
- Reorganized plugin directory structure to match Traefik's local plugin requirements
- Changed from remote plugin to local plugin configuration
- Plugin now loads successfully

**Directory Structure**:
```
KoolFlows/traefik/plugins-local/
├── src/
│   └── github.com/
│       └── maxlerebourg/
│           └── crowdsec-bouncer-traefik-plugin/
│               ├── bouncer.go
│               ├── .traefik.yml
│               ├── bouncer_test.go
│               └── ... (other plugin files)
```

**Configuration Changes**:
- `traefik.yml`: Changed from `experimental.plugins` to `experimental.localPlugins`
- `dynamic/config.yml`: Updated plugin reference from `crowdsec-bouncer-traefik-plugin` to `bouncer`
- `docker-compose.yml`: Re-added volume mount for `./KoolFlows/traefik/plugins-local:/plugins-local:ro`

**Status**: ✅ RESOLVED - Plugin now loads and initializes successfully

## Approaches Tried

### Approach 1: Remote Plugin Download
**Method**: Configure Traefik to download plugin from plugins.traefik.io

**Configuration**:
```yaml
experimental:
  plugins:
    bouncer:
      moduleName: github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin
      version: v1.4.7
```

**Result**: ❌ FAILED - Network timeout when downloading plugin
```
unable to install plugin bouncer: unable to download plugin
github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin: failed to call service:
Get "https://plugins.traefik.io/public/download/...": context deadline exceeded
(Client.Timeout exceeded while awaiting headers)
```

**Lesson**: Remote downloads not viable in this environment

---

### Approach 2: Local Plugin with Correct Directory Structure
**Method**: Use pre-cloned plugin from `plugins-local` directory with proper directory structure

**Configuration**:
```yaml
experimental:
  localPlugins:
    bouncer:
      moduleName: github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin
```

**Result**: ✅ SUCCESS - Plugin loads correctly

**Status Output**:
```
[90m2025-12-20T13:07:33Z[0m [32mINF[0m [1mLoading plugins...[0m [36mplugins=[0m["bouncer"]
[90m2025-12-20T13:07:33Z[0m [32mINF[0m [1mPlugins loaded.[0m [36mplugins=[0m["bouncer"]
```

---

### Approach 3: CrowdSec Enrollment (Blocked by ISP Firewall)
**Method**: Enroll security engine with CrowdSec Console via enrollment code

**Command**:
```bash
docker exec koolflows-crowdsec cscli console enroll -e context cmje7omiv000202jy3lt0d74j
```

**Result**: ❌ FAILED - ISP firewall blocks api.crowdsec.net
```
Error: cscli console enroll: could not enroll instance:
Post "https://api.crowdsec.net/v3/watchers/enroll": API error: Forbidden
```

**Analysis**:
- DNS resolution works from container
- TCP connection to api.crowdsec.net:443 times out
- ISP firewall is blocking outbound connections to CrowdSec infrastructure

---

## Configuration Changes Made

### 1. Traefik Static Configuration (`traefik.yml`)
**Change**: Updated access log format to JSON for better CrowdSec parsing
```yaml
accessLog:
  filePath: /var/log/traefik/access.log
  format: json
  filters:
    statusCodes:
      - "200-299"
      - "400-599"
  bufferingSize: 0
  fields:
    headers:
      defaultMode: drop
      names:
        User-Agent: keep
```

### 2. CrowdSec Acquisition Configuration (`crowdsec/config/acquis.yaml`)
**Change**: Added multiple log sources including syslog and AppSec
```yaml
# System logs
filenames:
  - /var/log/auth.log
  - /var/log/syslog
labels:
  type: syslog
---
# Traefik access logs
filenames:
  - /var/log/traefik/*.log
labels:
  type: traefik
---
# AppSec configuration
listen_addr: 0.0.0.0:7422
appsec_config: crowdsecurity/appsec-default
source: appsec
labels:
  type: appsec
```

### 3. CrowdSec Dockerfile
**Change**: Enhanced with proper initialization and AppSec support
- Added curl dependency
- Proper volume mounts for persistent data
- Collection installation during startup

### 4. Docker Compose (`docker-compose.yml`)
**Changes**:
- Removed `DISABLE_COLLECTIONS` environment variable (was preventing collection installation)
- Changed CrowdSec ports from tmpfs to persistent volume (`crowdsec_data`)
- Exposed AppSec port (7422)
- Added profiles.yaml volume mount
- Traefik dashboard port mapped to 8888 (to avoid conflict with CrowdSec API on 8080)
- Added CROWDSEC_BOUNCER_KEY environment variable for Traefik

### 5. Traefik Dynamic Configuration (`dynamic/config.yml`)
**Changes**:
- Changed plugin reference from `crowdsec-bouncer-traefik-plugin` to `bouncer`
- Changed mode from `stream` to `live`
- Added trusted IP ranges for private networks
- Updated middleware configuration

## Current Status

### ✅ WORKING
- Traefik container: Running and healthy
- CrowdSec plugin: Loads successfully in Traefik
- Local plugin infrastructure: Properly configured
- Basic Traefik routing: Functional
- Middleware pipeline: Configured and ready

### ❌ NOT WORKING (ISP Firewall Constraint)
- CrowdSec Cloud API access: Blocked by ISP firewall
- Watcher enrollment: Cannot authenticate with api.crowdsec.net
- GeoIP database downloads: Cannot reach hub-data.crowdsec.net
- CrowdSec automatic updates: Blocked

### ⚠️ DEGRADED MODE
- CrowdSec running in **local-only mode** (no cloud intelligence)
- Can still detect threats from local log analysis
- No access to community threat intelligence
- No automatic collection/parser updates

## Next Steps for Local-Only Mode

To proceed with local-only CrowdSec operation:

1. **Disable cloud API calls in CrowdSec**:
   ```bash
   # Edit CrowdSec config to disable CAPI
   docker exec koolflows-crowdsec \
     sed -i 's/enabled: true/enabled: false/' /etc/crowdsec/config.yaml
   ```

2. **Restart CrowdSec**:
   ```bash
   docker compose restart crowdsec
   ```

3. **Generate bouncer API key**:
   ```bash
   docker exec koolflows-crowdsec cscli bouncers list
   docker exec koolflows-crowdsec cscli bouncers inspect traefik-plugin
   ```

4. **Update Traefik with bouncer key**:
   - Export CROWDSEC_BOUNCER_KEY environment variable
   - Set in docker-compose.yml or via .env file
   - Restart Traefik

5. **Test integration**:
   - Verify no 403 errors in CrowdSec logs
   - Check Traefik middleware loads without errors
   - Test with simulated attacks to verify detection

## Future Workarounds if ISP Restriction is Lifted

If network access to CrowdSec API is later restored:

1. **Enable cloud API in CrowdSec config**
2. **Run enrollment command**:
   ```bash
   docker exec koolflows-crowdsec cscli console enroll -e context <ENROLLMENT_CODE>
   ```
3. **Update CrowdSec to remote plugin (optional)**:
   - Change back to remote plugin download if desired
   - Update traefik.yml to use `experimental.plugins` instead of `experimental.localPlugins`

## Network Requirements Summary

### For Full CrowdSec Operation (Currently Blocked)
```
Outbound HTTPS (port 443) to:
- api.crowdsec.net (IPs: 54.194.95.0, 34.250.8.127, 52.215.215.208)
  Purpose: Watcher enrollment, authentication, decision sync

- hub-data.crowdsec.net
  Purpose: GeoIP data, parsers, collections
```

### For Remote Traefik Plugins (Currently Blocked)
```
Outbound HTTPS (port 443) to:
- plugins.traefik.io
  Purpose: Plugin downloads
  Status: Worked around with local plugins
```

### Currently Working
```
Outbound HTTPS (port 443) to:
- github.com (accessible)
- Other general internet access (accessible)
```

## Key Files Modified

1. `/home/nkem/Desktop/itlds/mvp/KoolFlows/traefik/traefik.yml`
2. `/home/nkem/Desktop/itlds/mvp/KoolFlows/crowdsec/config/acquis.yaml`
3. `/home/nkem/Desktop/itlds/mvp/KoolFlows/crowdsec/Dockerfile`
4. `/home/nkem/Desktop/itlds/mvp/KoolFlows/traefik/dynamic/config.yml`
5. `/home/nkem/Desktop/itlds/mvp/docker-compose.yml`
6. Plugin directory: Reorganized from `plugins-local/crowdsec-bouncer-traefik-plugin` to `plugins-local/src/github.com/maxlerebourg/crowdsec-bouncer-traefik-plugin`

## Commands for Troubleshooting

**Check CrowdSec logs for API errors**:
```bash
docker logs koolflows-crowdsec 2>&1 | grep -i "error\|forbidden\|403"
```

**Check Traefik plugin loading status**:
```bash
docker logs koolflows-traefik 2>&1 | grep -i "plugin"
```

**List registered bouncers**:
```bash
docker exec koolflows-crowdsec cscli bouncers list
```

**Check CrowdSec health**:
```bash
docker exec koolflows-crowdsec cscli version
docker exec koolflows-crowdsec cscli metrics
```

**Monitor real-time logs**:
```bash
docker compose logs -f crowdsec traefik
```

**Check container health status**:
```bash
docker compose ps
```

## References

- Blog Post Used: https://blog.lrvt.de/configuring-crowdsec-with-traefik/
- CrowdSec Documentation: https://docs.crowdsec.net/
- Traefik Documentation: https://doc.traefik.io/traefik/
- CrowdSec Console: https://app.crowdsec.net/
