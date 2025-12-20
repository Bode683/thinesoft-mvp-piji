# QueWall Troubleshooting Guide

This guide covers common issues and their solutions.

## Prerequisites & Setup Issues

### "Docker is not installed or not in PATH"

**Symptom**: Setup script exits immediately with Docker error

**Solutions**:
- **Windows/macOS**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux**: Install Docker with your package manager:
  ```bash
  sudo apt-get install docker.io docker-compose
  sudo usermod -aG docker $USER  # Add user to docker group
  ```
- **Verify installation**:
  ```bash
  docker --version
  docker-compose --version
  ```

### "openssl is not installed or not in PATH"

**Symptom**: Setup script fails when generating secrets

**Solutions**:
- **Windows**: openssl is included with Git Bash; ensure you're running setup.sh from Git Bash
- **macOS**: Usually pre-installed; if missing:
  ```bash
  brew install openssl
  ```
- **Linux**: Install via package manager:
  ```bash
  sudo apt-get install openssl
  ```

### Setup script hangs or times out

**Symptom**: Script seems to hang after starting services

**Solutions**:
1. **Check system resources**
   - Ensure you have at least 2GB free RAM
   - Check disk space: `docker system df`

2. **Check individual service logs**
   ```bash
   docker-compose logs postgres
   docker-compose logs keycloak
   docker-compose logs oauth2-proxy
   ```

3. **Increase timeout in setup.sh** (if services are slow)
   - Edit line: `TIMEOUT=120` → increase to 180 or more
   - For Keycloak specifically, it can take 60+ seconds on slow systems

4. **Retry setup**
   ```bash
   ./teardown.sh --force
   ./setup.sh
   ```

## Network & Connectivity Issues

### "Cannot connect to keycloak.theddt.local"

**Symptom**: Browser shows "cannot reach this site" or "ERR_NAME_NOT_RESOLVED"

**Cause**: Hostname not added to hosts file

**Solution**:

1. **Verify hosts file entries**:

   **Linux/macOS**:
   ```bash
   cat /etc/hosts | grep theddt.local
   ```

   **Windows PowerShell**:
   ```powershell
   type C:\Windows\System32\drivers\etc\hosts | findstr theddt.local
   ```

2. **Add entries if missing**:

   **Linux/macOS** (use `sudo` for elevated privileges):
   ```bash
   sudo nano /etc/hosts
   # Add these lines:
   # 127.0.0.1 keycloak.theddt.local
   # 127.0.0.1 auth.theddt.local
   # 127.0.0.1 app.theddt.local
   ```

   **Windows** (open Notepad as Administrator):
   - Edit: `C:\Windows\System32\drivers\etc\hosts`
   - Add:
     ```
     127.0.0.1 keycloak.theddt.local
     127.0.0.1 auth.theddt.local
     127.0.0.1 app.theddt.local
     ```

3. **Clear DNS cache**:

   **Windows**:
   ```powershell
   ipconfig /flushdns
   ```

   **macOS**:
   ```bash
   sudo dscacheutil -flushcache
   ```

   **Linux**:
   ```bash
   sudo systemctl restart systemd-resolved
   ```

4. **Test connectivity**:
   ```bash
   ping keycloak.theddt.local
   curl http://keycloak.theddt.local/health/ready
   ```

### "Port 80 is already in use"

**Symptom**: Setup fails with "port is already allocated" error

**Solutions**:

1. **Find what's using port 80**:

   **Linux/macOS**:
   ```bash
   sudo lsof -i :80
   ```

   **Windows PowerShell**:
   ```powershell
   netstat -ano | findstr :80
   tasklist | findstr <PID>  # Replace <PID> with process ID
   ```

2. **Stop the conflicting service**:
   - If it's another Docker container: `docker stop <container_name>`
   - If it's another application: Stop it through system settings or task manager

3. **Alternative**: Modify docker-compose.yml to use different port:
   ```yaml
   traefik:
     ports:
       - "8000:80"  # Use port 8000 instead of 80
   ```
   Then access services on different hostnames/ports:
   - `http://keycloak.theddt.local:8000`

### "Port 8080 is already in use"

**Symptom**: Setup fails on Traefik dashboard port

**Solutions**: Same as port 80 above, modify docker-compose.yml:
```yaml
traefik:
  ports:
    - "8000:80"
    - "9090:8080"  # Use port 9090 for dashboard
```

### Port 5432 (PostgreSQL) conflicts

**Symptom**: "Address already in use" for port 5432

**Note**: PostgreSQL is not exposed externally in this setup (only accessible from other containers)

**Solution**: This usually means another PostgreSQL instance is running
```bash
docker ps | grep postgres
# Stop any conflicting PostgreSQL containers
docker stop <container_id>
```

## Service Health Issues

### PostgreSQL not starting

**Symptom**: Keycloak fails to start with database connection error

**Check logs**:
```bash
docker-compose logs postgres
```

**Common solutions**:

1. **Permissions issue**:
   ```bash
   docker-compose down -v  # Remove volumes
   ./setup.sh              # Restart
   ```

2. **Volume conflict**:
   ```bash
   docker volume ls | grep postgres
   docker volume rm <volume_name>
   ./setup.sh
   ```

3. **Corrupt volume**:
   ```bash
   ./teardown.sh --force --clean-volumes
   ./setup.sh
   ```

### Keycloak taking too long to start

**Symptom**: Setup script times out waiting for Keycloak health check

**Keycloak startup is slow** (expected behavior):
- First startup: 30-60 seconds
- Realm import: adds 10-20 seconds
- Slow systems: can take 2+ minutes

**Solutions**:

1. **Increase setup timeout**:
   - Edit setup.sh: Change `TIMEOUT=120` to `TIMEOUT=180`

2. **Monitor Keycloak startup manually**:
   ```bash
   docker-compose logs -f keycloak
   # Wait for: "Keycloak X.X.X on Quarkus Y.Y.Y started in XXXms"
   ```

3. **Check for import errors**:
   ```bash
   docker-compose logs keycloak | grep -i error
   ```

4. **Verify realm export is valid**:
   ```bash
   # Check if generated file exists
   ls -la keycloak/realm-export-generated.json
   # Validate JSON
   cat keycloak/realm-export-generated.json | python3 -m json.tool > /dev/null
   ```

### oauth2-proxy not healthy

**Symptom**: "oauth2-proxy failed to become healthy" error

**Likely cause**: Keycloak not ready or discovery endpoint not accessible

**Solutions**:

1. **Check Keycloak readiness**:
   ```bash
   curl http://localhost:8080/health/ready
   # Should return JSON with "status": "UP"
   ```

2. **Verify OIDC discovery endpoint**:
   ```bash
   curl http://keycloak:8080/realms/theddt/.well-known/openid-configuration
   # From inside oauth2-proxy container:
   docker-compose exec oauth2-proxy curl http://keycloak:8080/realms/theddt/.well-known/openid-configuration
   ```

3. **Check oauth2-proxy logs**:
   ```bash
   docker-compose logs oauth2-proxy
   ```

4. **Manual wait for Keycloak**:
   ```bash
   # Stop everything, restart in correct order
   ./teardown.sh --force
   docker-compose up -d postgres
   # Wait 10 seconds
   sleep 10
   docker-compose up -d keycloak
   # Wait 60 seconds
   sleep 60
   docker-compose up -d oauth2-proxy oauth2-proxy traefik whoami
   ```

### Traefik dashboard not accessible

**Symptom**: Cannot access http://localhost:8080

**Solutions**:

1. **Check Traefik is running**:
   ```bash
   docker-compose ps | grep traefik
   ```

2. **Verify ports**:
   ```bash
   netstat -tulpn | grep 8080
   ```

3. **Check Traefik logs**:
   ```bash
   docker-compose logs traefik
   ```

4. **Restart Traefik**:
   ```bash
   docker-compose restart traefik
   ```

## Authentication Flow Issues

### "302 redirect loops" or immediate redirect

**Symptom**: Accessing app redirects to login, but login loop continues

**Causes**:
- oauth2-proxy not ready
- Session cookie domain mismatch
- Client secret mismatch

**Solutions**:

1. **Wait for oauth2-proxy to be fully ready**:
   ```bash
   # Wait 30-60 seconds after setup completes
   docker-compose logs oauth2-proxy | tail -20
   # Look for: "Server is running..."
   ```

2. **Clear browser cookies**:
   - Chrome: DevTools > Application > Cookies > delete oauth2proxy_*
   - Firefox: Preferences > Privacy > Cookies > Clear Data for theddt.local
   - Or use incognito/private window

3. **Verify client secret matches**:
   ```bash
   cat secrets/oauth2_client_secret.txt
   # Should match the secret in Keycloak realm config
   ```

4. **Check Keycloak admin console**:
   - Go to http://keycloak.theddt.local
   - Login with admin / <password_from_secrets>
   - Realm: theddt → Clients → oauth2-proxy-client
   - Verify Secret matches `secrets/oauth2_client_secret.txt`

### Login page appears but credentials rejected

**Symptom**: Keycloak login form shows but login fails

**Usual cause**: Wrong password or user doesn't exist

**Solutions**:

1. **Verify test user exists**:
   - Go to Keycloak: http://keycloak.theddt.local
   - Login with admin credentials
   - Realm: theddt → Users
   - Should see "testuser"

2. **Reset test user password**:
   - Click on testuser → Credentials tab
   - Set password to: `password123`
   - Disable "Temporary" option
   - Save

3. **Create new test user**:
   - Users → Add User → testuser2
   - Set password
   - Set Email Verified: ON
   - Save

### Login succeeds but stuck on oauth2-proxy callback

**Symptom**: After login, page goes to oauth2-proxy callback URL and hangs

**Likely cause**: oauth2-proxy cannot reach Keycloak on the token endpoint

**Solutions**:

1. **Verify oauth2-proxy environment variables**:
   ```bash
   docker-compose config | grep -A 20 "oauth2-proxy:" | grep OIDC
   ```

2. **Test from inside oauth2-proxy container**:
   ```bash
   docker-compose exec oauth2-proxy bash
   # Inside container:
   curl -v http://keycloak:8080/realms/theddt/.well-known/openid-configuration
   ```

3. **Check oauth2-proxy logs during login**:
   ```bash
   docker-compose logs -f oauth2-proxy
   # Attempt login and watch for errors
   ```

4. **Verify network connectivity**:
   ```bash
   docker-compose exec oauth2-proxy ping keycloak
   ```

### Header injection not working

**Symptom**: Application doesn't receive X-Auth-Request-* headers

**Causes**:
- ForwardAuth middleware not configured
- Traefik not forwarding headers
- Service not reading headers

**Solutions**:

1. **Verify Traefik middleware is configured**:
   ```bash
   docker-compose exec traefik curl http://localhost:15000/api/rawdata | grep -i oauth2-auth
   ```

2. **Check service is using the middleware**:
   ```bash
   docker-compose logs traefik | grep -i middleware | head -20
   ```

3. **Verify whoami service shows headers**:
   ```bash
   # Authenticate first, then:
   curl -H "Cookie: oauth2proxy_=<session_cookie>" http://app.theddt.local
   ```

4. **Manually test ForwardAuth endpoint**:
   ```bash
   # From authenticated browser session, get cookie value
   # Then test:
   curl -v -H "Cookie: oauth2proxy_=<cookie>" http://localhost:4180/oauth2/auth
   # Should return 200 with X-Auth-Request-* headers
   ```

## Log Inspection

### View service logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs keycloak
docker-compose logs oauth2-proxy
docker-compose logs traefik

# Follow logs in real-time
docker-compose logs -f <service>

# Last 100 lines
docker-compose logs --tail=100 <service>

# Logs with timestamps
docker-compose logs -t <service>
```

### Check container status

```bash
# See running containers
docker-compose ps

# Detailed container info
docker-compose ps -a

# Container details
docker inspect <container_name>

# Resource usage
docker stats
```

### Test endpoints directly

```bash
# Test Keycloak health
curl http://localhost:8080/health/ready

# Test oauth2-proxy health
curl http://localhost:4180/ping

# Test discovery endpoint
curl http://keycloak:8080/realms/theddt/.well-known/openid-configuration

# Test from inside a container
docker-compose exec <service> curl http://<other-service>:port/path
```

## Advanced Debugging

### Inspect Docker network

```bash
# List networks
docker network ls

# Inspect quewall-network
docker network inspect quewall-network
```

### Check secret contents

```bash
# View secrets (be careful with passwords)
cat secrets/keycloak_admin_password.txt
cat secrets/postgres_password.txt
cat secrets/oauth2_client_secret.txt

# Do NOT commit these to version control!
```

### Validate configuration files

```bash
# Check docker-compose.yml syntax
docker-compose config > /dev/null && echo "Valid"

# Check realm export JSON
python3 -m json.tool keycloak/realm-export-generated.json > /dev/null && echo "Valid JSON"
```

### Clean up and restart

```bash
# Complete fresh start
./teardown.sh --force --clean-secrets
rm -rf volumes/  # if any
docker system prune -a  # WARNING: removes all unused Docker resources
./setup.sh

# Or more conservatively
./teardown.sh --force
./setup.sh  # Reuses existing secrets
```

## Permission Issues

### "Permission denied" on setup.sh

**Symptom**: `bash: ./setup.sh: Permission denied`

**Solutions**:

```bash
# Make executable
chmod +x setup.sh teardown.sh

# Or run with bash explicitly
bash setup.sh
bash teardown.sh
```

### Docker permission denied

**Symptom**: `Got permission denied while trying to connect to Docker daemon`

**Solutions**:

```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker  # Activate new group
docker ps      # Test

# Or use sudo
sudo docker-compose up
```

## Windows-Specific Issues

### Scripts don't work on Windows CMD

**Symptom**: setup.sh/teardown.sh don't work in Command Prompt or PowerShell

**Solutions**:
1. Use **Git Bash** (included with Git for Windows)
2. Or use **WSL2** (Windows Subsystem for Linux 2)
3. Or create PowerShell versions of scripts

### Line ending issues (CRLF vs LF)

**Symptom**: Script fails with weird errors about line endings

**Solutions**:
```bash
# Convert line endings (in Git Bash)
dos2unix setup.sh teardown.sh

# Or use sed
sed -i 's/\r$//' setup.sh teardown.sh
```

## Reaching Out for Help

If your issue isn't covered:

1. **Collect diagnostics**:
   ```bash
   docker-compose ps -a
   docker-compose logs > logs.txt 2>&1
   docker network inspect quewall-network > network.txt 2>&1
   docker volume ls > volumes.txt 2>&1
   ```

2. **Check Docker logs**:
   ```bash
   docker system events > events.log &
   # Reproduce issue
   # Stop with Ctrl+C
   ```

3. **Review relevant documentation**:
   - See docs/ARCHITECTURE.md for component details
   - Check README.md for configuration options
   - Review service-specific docs:
     - [Traefik Docs](https://doc.traefik.io/)
     - [Keycloak Docs](https://www.keycloak.org/docs/latest/)
     - [oauth2-proxy Docs](https://oauth2-proxy.github.io/oauth2-proxy/)

## Common Mistakes

1. **Using wrong password**
   - Test user: `testuser` / `password123` ✓
   - Admin user: `admin` / (check `secrets/keycloak_admin_password.txt`)

2. **Not adding hosts entries**
   - Must add to /etc/hosts or C:\Windows\System32\drivers\etc\hosts
   - localhost/127.0.0.1 won't work by itself

3. **Running from wrong directory**
   - Always run setup.sh/teardown.sh from QueWall root directory
   - Docker-compose.yml must be in current directory

4. **Using old setup**
   - Always run setup.sh from scratch: `./teardown.sh --force && ./setup.sh`
   - Don't try to update containers individually

5. **Trying to use HTTPS on HTTP-only MVP**
   - This is development setup; use http:// not https://
   - For production, enable TLS

## Performance & Optimization

### Startup time too slow

- **Expected first startup**: 60-120 seconds
- **Subsequent startups**: 30-60 seconds

**Optimize**:
- Use SSD for Docker storage
- Allocate more Docker resources (Preferences > Resources on Desktop)
- Close other applications to free RAM

### Memory usage high

**Check usage**:
```bash
docker stats
```

**Reduce**:
- Stop unnecessary containers
- Reduce Keycloak cache (advanced configuration)
- Use lighter database image

## Final Resort

If nothing works:

1. **Complete cleanup**:
   ```bash
   ./teardown.sh --force --clean-secrets
   docker system prune -a --volumes
   ```

2. **Reinstall Docker** (nuclear option):
   - Uninstall Docker completely
   - Restart computer
   - Reinstall Docker
   - Run setup.sh again

3. **Check system health**:
   ```bash
   # Sufficient free space?
   df -h /var  # Linux

   # Sufficient RAM?
   free -h  # Linux
   ```
