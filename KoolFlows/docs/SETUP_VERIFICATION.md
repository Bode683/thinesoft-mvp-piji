# KoolFlows Setup Verification Checklist

This document helps verify that the KoolFlows CrowdSec + Traefik setup is complete and ready for team members to use.

## ✅ Files Updated for New Implementation

### Core Setup Files
- [x] `setup.sh` - Now generates `.env` file with CROWDSEC_BOUNCER_KEY
- [x] `.env.example` - Created as template for environment variables
- [x] `.gitignore` - Already includes `.env` (not committed to version control)
- [x] `docker-compose.yml` - Updated with correct port mappings and configuration

### Traefik Configuration
- [x] `KoolFlows/traefik/traefik.yml` - Updated to use local plugins and JSON logging
- [x] `KoolFlows/traefik/dynamic/config.yml` - Updated middleware configuration for bouncer plugin
- [x] `KoolFlows/traefik/plugins-local/` - Properly structured for local plugin discovery

### CrowdSec Configuration
- [x] `KoolFlows/crowdsec/Dockerfile` - Cleaned up, uses custom entrypoint
- [x] `KoolFlows/crowdsec/entrypoint.sh` - Updated to disable cloud API for local-only mode
- [x] `KoolFlows/crowdsec/config/acquis.yaml` - Updated for JSON log parsing
- [x] `KoolFlows/crowdsec/config/profiles.yaml` - Decision profiles in place
- [x] `KoolFlows/crowdsec/config/appsec.yaml` - AppSec/WAF configuration available

### Documentation
- [x] `KoolFlows/README.md` - Updated with new architecture and configuration details
- [x] `KoolFlows/TROUBLESHOOTING.md` - Complete troubleshooting guide and issue analysis
- [x] `KoolFlows/SETUP_COMPLETE.md` - Operational setup documentation

## 🔍 Pre-Setup Verification

Before team members run `setup.sh`, verify:

- [ ] Docker is installed and running: `docker --version`
- [ ] Docker Compose is available: `docker compose version`
- [ ] Project directory structure exists: `ls -la`
- [ ] No existing `.env` file (or backup if it exists)

## 🚀 Setup Process for Team Members

1. **Ensure Prerequisites**
   ```bash
   docker --version
   docker compose version
   ```

2. **Run Setup Script** (from project root)
   ```bash
   ./setup.sh
   ```
   This will:
   - Check Docker and Docker Compose availability
   - Create directory structure
   - Generate secrets in `secrets/` directory
   - **Generate `.env` file with CROWDSEC_BOUNCER_KEY**
   - Create Docker network `web`
   - Build custom images
   - Start all services
   - Wait for health checks
   - Display summary with credentials

3. **Add DNS Entries** (as prompted by setup.sh)
   Edit `/etc/hosts` and add:
   ```
   127.0.0.1 theddt.local
   127.0.0.1 pgadmin.theddt.local
   127.0.0.1 traefik.theddt.local
   ```

4. **Verify Services Started**
   ```bash
   docker compose ps
   ```
   Expected output:
   - `koolflows-traefik` - Up (health: starting → healthy)
   - `koolflows-crowdsec` - Up (healthy)
   - Other services from PeSquel stack

## ✅ Post-Setup Verification

After setup.sh completes, verify the configuration:

### Check Environment Variables
```bash
# Verify .env file exists and contains the bouncer key
cat .env
```
Expected output:
```
# CrowdSec Bouncer API Key
CROWDSEC_BOUNCER_KEY=<random_base64_key>
```

### Check File Permissions
```bash
# .env should have restricted permissions
ls -la .env
# Expected: -rw------- (600)

# Secrets should be readable
ls -la secrets/
```

### Verify CrowdSec Configuration
```bash
# Check bouncer key is set in secrets
cat secrets/crowdsec_bouncer_key.txt

# Verify bouncer registration
docker exec koolflows-crowdsec cscli bouncers list
```
Expected output: bouncers named `traefik-plugin` and `traefik-local`

### Verify Traefik Plugin Loads
```bash
# Check if bouncer plugin loads successfully
docker logs koolflows-traefik | grep -i "plugin"
```
Expected output:
```
Loading plugins...["bouncer"]
Plugins loaded.
```

### Verify Middleware Configuration
```bash
# Check if middleware is properly configured
docker logs koolflows-traefik | grep -i "middleware"
```

### Test Traefik Routing
```bash
# Should get 404 (no route configured, but Traefik is responding)
curl http://localhost/

# Should work (health endpoint)
curl -H "Host: health.theddt.local" http://localhost/
```

### Check CrowdSec Health
```bash
# CrowdSec should be healthy
docker exec koolflows-crowdsec cscli version

# Check metrics
docker exec koolflows-crowdsec cscli metrics
```

## ⚠️ Known Expected Behaviors

### Traefik Health Check Status
- **May show as "unhealthy"** - This is due to Docker socket timeout, NOT a real issue
- **Service IS operational** - Test with curl to verify
- This does NOT affect functionality

### CrowdSec Cloud API 403 Errors
- **Expected in local-only mode** - ISP firewall blocks api.crowdsec.net
- **Does NOT affect threat detection** - Local threat detection works fine
- See `TROUBLESHOOTING.md` for details

### Startup Times
- **CrowdSec**: 30-60 seconds before healthy (first-run initialization)
- **Traefik**: 10-20 seconds to establish Docker socket connection
- **Services depend on each other**, so startup order may take time

## 🐛 Troubleshooting Setup Issues

### Issue: Docker network 'web' already exists
**Solution**: This is fine, setup.sh handles this gracefully

### Issue: `.env` file already exists
**Solution**:
```bash
# Remove old .env and re-run setup
rm .env
./setup.sh
```

### Issue: Services not starting
**Solution**: Check logs
```bash
docker compose logs traefik
docker compose logs crowdsec
```

### Issue: CROWDSEC_BOUNCER_KEY not set
**Solution**:
```bash
# Verify .env exists
cat .env

# If missing, re-run setup
rm .env
./setup.sh
```

### Issue: Permission denied on .env
**Solution**:
```bash
# Fix permissions
chmod 600 .env
```

## 📋 Setup.sh Changes Summary

The `setup.sh` script has been updated with the following changes:

### New Function: `create_env_file()`
- Generates `.env` file with CROWDSEC_BOUNCER_KEY
- Reads key from `secrets/crowdsec_bouncer_key.txt`
- Sets correct permissions (600)
- Logs the creation timestamp

### Updated: `generate_secrets()`
- Now stores the generated bouncer key in a variable
- Reuses the key if secrets already exist
- Passes key to new `create_env_file()` function

### Updated: `main()`
- Calls `create_env_file()` after `generate_secrets()`
- Ensures `.env` is created before containers start
- Allows Traefik to read CROWDSEC_BOUNCER_KEY at startup

## 🔐 Security Notes

### .env File Security
- Contains sensitive API keys
- Should NOT be committed to version control (already in .gitignore)
- Set with restrictive permissions (mode 600)
- Each team member gets their own generated key

### Secrets Management
- All sensitive data goes to `.env` (for runtime)
- Pre-generated keys go to `secrets/` (for Docker secrets)
- Docker secrets are isolated to containers via `/run/secrets/`

### Local-Only Mode Security
- CrowdSec cannot reach cloud API (by design)
- Local threat detection still fully functional
- No external dependencies for basic operation
- Reduced attack surface (no outbound cloud calls)

## 📚 Documentation for Team

Team members should read in this order:

1. **This file** - Setup verification and troubleshooting
2. **README.md** - Architecture and service descriptions
3. **SETUP_COMPLETE.md** - Operational guide for running services
4. **TROUBLESHOOTING.md** - Detailed issue analysis and workarounds

## ✅ Team Onboarding Checklist

For each new team member:

- [ ] Provide project repository access
- [ ] Have them clone the project
- [ ] Have them read this document (SETUP_VERIFICATION.md)
- [ ] Have them run `./setup.sh`
- [ ] Have them verify services with `docker compose ps`
- [ ] Have them test with `curl http://localhost/`
- [ ] Provide credentials (displayed at end of setup.sh)
- [ ] Direct them to README.md for operations guide

## 🎯 Next Steps

After successful setup:

1. **Add your backend services** to docker-compose.yml
2. **Configure Traefik routing** with Docker labels
3. **Add DNS entries** to `/etc/hosts` for new services
4. **Monitor logs** with `docker compose logs -f`
5. **Check CrowdSec decisions** with `docker exec koolflows-crowdsec cscli decisions list`

## 📞 Support

If team members encounter issues:

1. Check the **Troubleshooting** section in this file
2. Check `KoolFlows/TROUBLESHOOTING.md` for detailed analysis
3. Check logs with `docker compose logs [service]`
4. Verify `.env` file exists and has correct permissions
5. Re-run setup if necessary: `./setup.sh`

---

**Last Updated**: 2025-12-20
**Status**: Ready for Team Use
