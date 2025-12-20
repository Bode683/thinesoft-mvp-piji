# PeSquel Microservice - Database Layer

A Docker-based database microservice featuring **PostgreSQL 17** (relational database), **pgBouncer** (connection pooling), and **pgAdmin** (database management UI). This is the data persistence layer of the ITLDS MVP stack.

## Architecture

```
┌──────────────────────────────────────┐
│      pgAdmin (Database UI)           │
│  Port 80 (via Traefik routing)       │
└──────────┬───────────────────────────┘
           │
    ┌──────┴──────────┐
    │                 │
┌───▼─────────┐  ┌───▼──────────────┐
│ PostgreSQL  │  │  pgBouncer       │
│ Port 5432   │  │  Port 6432       │
│ (Direct)    │  │  (Pooled)        │
└─────────────┘  └──────────────────┘

Docker Network: web (bridge mode)
```

## Services Overview

| Service | Role | Port | Notes |
|---------|------|------|-------|
| **PostgreSQL 17** | Relational database | 5432 | Alpine-based, data persisted to `./postgres/data`; custom entrypoint for dynamic password |
| **pgBouncer 1.23** | Connection pooler | 6432 (internal) | Transaction pooling mode; MD5 authentication; protects Postgres from connection storms |
| **pgAdmin 4** | Web-based DB management | 80 (via Traefik) | Routed to `pgadmin.theddt.local`; persists configuration and connection definitions |

## Prerequisites

- **Docker Desktop for Windows** with WSL 2 backend enabled
- **Git Bash** or **WSL** for running shell scripts
- **Administrator access** to edit the hosts file
- At least **2GB of available disk space**
- Ports **80, 5432, 3000, 8080** available on localhost

## Quick Start

### 1. Prerequisites Check

Ensure Docker Desktop is running with WSL 2 backend:
- Open Docker Desktop
- Check Settings > Resources > Docker Engine
- Verify "Use the WSL 2 based engine" is enabled

Add project directory to Docker file sharing (if needed):
- Settings > Resources > File Sharing
- Add `C:\Users\nkema\Desktop\itlds\mvp\PeSquel`

### 2. Run Setup Script

Open Git Bash or WSL terminal in the project directory:

```bash
cd C:\Users\nkema\Desktop\itlds\mvp\PeSquel
bash setup.sh
```

The script will:
- Verify Docker is running
- Generate secure secrets for all services
- Create necessary directories
- Generate pgBouncer password hash
- **Pause for manual hosts file editing** (important!)
- Create Docker network
- Pull Docker images
- Start all services

### 3. Update Hosts File (Manual Step)

When the setup script pauses, open the hosts file with administrator privileges:

**Windows:**
1. Right-click Notepad → "Run as administrator"
2. File → Open → Navigate to `C:\Windows\System32\drivers\etc\hosts`
3. Add these lines at the end:

```
127.0.0.1 theddt.local
127.0.0.1 api.theddt.local
127.0.0.1 pgadmin.theddt.local
127.0.0.1 traefik.theddt.local
```

4. Save and return to terminal
5. Press Enter in the setup script to continue

**Alternative (PowerShell as Admin):**
```powershell
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "127.0.0.1 theddt.local"
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "127.0.0.1 api.theddt.local"
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "127.0.0.1 pgadmin.theddt.local"
Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value "127.0.0.1 traefik.theddt.local"
```

### 4. Access Services

Once setup completes, services are available at:

- **PostgREST API**: http://api.theddt.local
- **pgAdmin UI**: http://pgadmin.theddt.local
- **Traefik Dashboard**: http://traefik.theddt.local:8080
- **PostgreSQL**: localhost:5432 (direct connection)

## Testing the API

### Get All Todos

```bash
curl http://api.theddt.local/todos
```

### Create a Todo

```bash
curl -X POST http://api.theddt.local/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "My first todo", "completed": false}'
```

### View OpenAPI Documentation

```bash
curl http://api.theddt.local/
```

Or visit `http://api.theddt.local/` in your browser to see the interactive API documentation.

### Update a Todo

```bash
# First, get a todo to find its UUID
curl http://api.theddt.local/todos | jq '.[0].id'

# Then update it
curl -X PATCH http://api.theddt.local/todos?id=eq.YOUR_UUID_HERE \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

### Delete a Todo

```bash
curl -X DELETE http://api.theddt.local/todos?id=eq.YOUR_UUID_HERE
```

### Using pgAdmin

1. Navigate to http://pgadmin.theddt.local
2. Login with credentials from setup output:
   - Email: `admin@theddt.local`
   - Password: (shown in setup script output)
3. Create a server connection:
   - Host: `postgres` (container name)
   - Port: `5432`
   - Username: (shown in setup script output)
   - Password: (shown in setup script output)
   - Database: `pesequel_db`

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize as needed:

```bash
cp .env.example .env
```

Edit `.env` with your preferred values.

### Database Schema

The API schema is defined in `postgres/init/02-create-schema.sql`. To add new tables:

1. Edit `postgres/init/02-create-schema.sql`
2. Add your table definitions before the RLS policy section
3. Ensure tables are in the `api` schema
4. Run teardown and setup again to reinitialize:

```bash
bash teardown.sh  # Choose to delete volumes
bash setup.sh
```

### Secrets

All secrets are stored in `./secrets/` with restricted permissions (600):

- `postgres_user.txt` - PostgreSQL username
- `postgres_password.txt` - PostgreSQL password
- `postgres_db.txt` - Default database name
- `pgadmin_email.txt` - pgAdmin login email
- `pgadmin_password.txt` - pgAdmin login password
- `jwt_secret.txt` - PostgREST JWT signing secret (64 chars)

These files are automatically generated by `setup.sh` and excluded from Git.

## Security Features

### Row-Level Security (RLS)

All tables in the `api` schema have RLS enabled with policies:

```sql
ALTER TABLE api.todos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous read" ON api.todos
  FOR SELECT TO api_anon USING (true);
```

This enforces permissions at the database level.

### Database Roles

- **postgres**: Superuser (admin only)
- **authenticator**: Connection role for PostgREST (NOINHERIT)
- **api_anon**: Anonymous/unauthenticated requests (limited permissions)

### Docker Secrets

- All credentials stored in `./secrets/` directory
- Mounted read-only at `/run/secrets/` in containers
- Not visible in `docker inspect` output
- Secrets file permissions: 600 (owner read/write only)

### JWT Authentication

PostgREST validates JWT tokens:
- Minimum secret length: 32 characters
- Generated secret: 64 characters (strong)
- Supports HS256, HS384, HS512 algorithms
- Claims can map to PostgreSQL roles

## Docker Compose Structure

### Networks

- **web**: Bridge network connecting all services

### Volumes

- **postgres_data**: Bind mount to `./postgres-data` for persistent database storage
- **pgadmin_data**: Named volume for pgAdmin configuration persistence

### Service Dependencies

- **pgbouncer** depends on **postgres** (healthy)
- **postgrest** depends on **pgbouncer** (healthy)
- **pgadmin** depends on **postgres** (healthy)

All services restart automatically unless-stopped.

## Troubleshooting

### Issue: Can't Access Services via Hostname

**Symptoms:** Browser shows "Cannot reach api.theddt.local" or similar

**Solutions:**
1. Verify hosts file entries are correct:
   ```bash
   ping theddt.local
   ```

2. Check hosts file for typos:
   ```powershell
   Get-Content C:\Windows\System32\drivers\etc\hosts | grep theddt
   ```

3. Clear DNS cache:
   ```powershell
   ipconfig /flushdns
   ```

4. Verify Traefik is running:
   ```bash
   docker compose ps traefik
   ```

### Issue: Services Not Starting

**Symptoms:** `docker compose ps` shows containers exiting

**Solutions:**
1. Check Docker is running:
   ```bash
   docker ps
   ```

2. Check logs:
   ```bash
   docker compose logs -f
   ```

3. Check disk space:
   ```bash
   docker system df
   ```

4. Check port conflicts:
   ```powershell
   netstat -ano | findstr :80
   netstat -ano | findstr :5432
   netstat -ano | findstr :3000
   ```

### Issue: Database Connection Errors

**Symptoms:** PostgREST or pgAdmin can't connect to PostgreSQL

**Solutions:**
1. Verify PostgreSQL is healthy:
   ```bash
   docker compose ps postgres
   docker compose logs postgres
   ```

2. Check pgBouncer logs:
   ```bash
   docker compose logs pgbouncer
   ```

3. Test direct PostgreSQL connection:
   ```bash
   docker compose exec postgres psql -U pesequel_user -d pesequel_db -c "SELECT 1"
   ```

### Issue: PostgreSQL Init Scripts Not Running

**Symptoms:** Tables don't exist, schema not created

**Solutions:**
1. Init scripts only run on first start with empty data directory
2. To reinitialize:
   ```bash
   bash teardown.sh  # Choose to delete volumes
   bash setup.sh
   ```

3. Check init script logs:
   ```bash
   docker compose logs postgres | grep -A5 "sql"
   ```

### Issue: pgBouncer Authentication Failed

**Symptoms:** PostgREST or pgAdmin show connection pool authentication errors

**Solutions:**
1. Verify pgbouncer/userlist.txt exists and has content:
   ```bash
   cat pgbouncer/userlist.txt
   ```

2. Regenerate userlist:
   ```bash
   bash setup.sh
   ```

3. Check pgBouncer logs:
   ```bash
   docker compose logs pgbouncer
   ```

### Issue: PostgREST Returns 404 for API Endpoints

**Symptoms:** `curl http://api.theddt.local/todos` returns 404

**Solutions:**
1. Verify `api` schema exists:
   ```bash
   docker compose exec postgres psql -U pesequel_user -d pesequel_db -c "\dn api"
   ```

2. Verify tables in api schema:
   ```bash
   docker compose exec postgres psql -U pesequel_user -d pesequel_db -c "\dt api.*"
   ```

3. Check PostgREST logs:
   ```bash
   docker compose logs postgrest
   ```

4. Verify PostgREST can connect to pgBouncer:
   ```bash
   docker compose logs postgrest | grep -i "connect\|error"
   ```

### Issue: Permission Denied on Secrets

**Symptoms:** Containers fail to start with "Permission denied" reading secrets

**Solutions:**
1. Check secret file permissions:
   ```bash
   ls -l secrets/
   ```

2. Fix permissions:
   ```bash
   chmod 600 secrets/*.txt
   ```

3. Regenerate secrets:
   ```bash
   bash teardown.sh  # Choose to remove secrets
   bash setup.sh
   ```

## Performance Tuning

### pgBouncer Pool Settings

Edit `pgbouncer/pgbouncer.ini`:

```ini
default_pool_size = 20      # Connections per database/user
max_client_conn = 1000      # Maximum client connections
reserve_pool_size = 5       # Extra connections for emergencies
pool_mode = transaction     # Create new connection per transaction
```

### PostgREST Connection Pool

Edit `docker-compose.yml` postgrest environment:

```yaml
PGRST_DB_POOL: "10"                    # Connection pool size
PGRST_DB_POOL_ACQUISITION_TIMEOUT: "10" # Timeout in seconds
```

### PostgreSQL Configuration

For production, adjust `postgresql.conf`:
- `max_connections`: Maximum database connections
- `shared_buffers`: Memory for caching
- `effective_cache_size`: RAM available for caching

## Logs and Monitoring

### View Service Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f postgres
docker compose logs -f postgrest
docker compose logs -f pgbouncer
docker compose logs -f pgadmin
docker compose logs -f traefik
```

### Check Service Health

```bash
docker compose ps
```

Each service shows its status (Up, Exited, etc.) and health status if applicable.

### Monitor Resource Usage

```bash
docker stats
```

Shows real-time CPU, memory, and network usage for each container.

## Common Tasks

### Add a New Table

1. Edit `postgres/init/02-create-schema.sql`
2. Add table definition in the `api` schema:

```sql
CREATE TABLE IF NOT EXISTS api.users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE api.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous read" ON api.users
  FOR SELECT TO api_anon USING (true);

GRANT SELECT ON api.users TO api_anon;
```

3. Reinitialize database:
```bash
bash teardown.sh  # Choose to delete volumes
bash setup.sh
```

### Connect with psql CLI

```bash
psql -h localhost -U pesequel_user -d pesequel_db
```

When prompted for password, use the value from `secrets/postgres_password.txt`:

```bash
cat secrets/postgres_password.txt
```

### Reset Everything and Start Fresh

```bash
bash teardown.sh
# Answer "y" to all prompts to delete data and secrets
bash setup.sh
```

### Update Hosts File Later

If you need to add more domains:

```bash
# In Notepad (as admin) or PowerShell (as admin)
# Edit C:\Windows\System32\drivers\etc\hosts
# Add: 127.0.0.1 yourdomain.theddt.local

# Clear DNS cache
ipconfig /flushdns
```

## Cleanup

To stop all services and remove containers:

```bash
bash teardown.sh
```

The script will prompt you to optionally:
- Remove volumes (deletes all database data)
- Remove Docker network
- Remove secrets

To preserve data while stopping services:
```bash
docker compose down
```

To completely remove everything including data:
```bash
docker compose down -v
rm -rf postgres-data pgadmin-data
rm secrets/*.txt
docker network rm web
```

## Windows-Specific Notes

### File Sharing Issues

If containers can't access files:
1. Open Docker Desktop Settings
2. Go to Resources > File Sharing
3. Add `C:\Users\nkema\Desktop\itlds\mvp\PeSquel`
4. Click "Apply & Restart"

### Line Endings

The project uses `.gitattributes` to enforce LF line endings:

```bash
git config --global core.autocrlf input
```

This prevents CRLF line ending issues in shell scripts.

### WSL 2 Performance

For best performance:
- Store project files in WSL filesystem if possible
- Or use named volumes instead of bind mounts
- WSL 2 is significantly faster than Hyper-V

## Next Steps After MVP

1. **Add JWT Authentication**
   - Create user login endpoint
   - Generate JWT tokens
   - Map JWT claims to PostgreSQL roles
   - Add authenticated API endpoints

2. **Extend Database Schema**
   - Add application-specific tables
   - Implement database migrations
   - Create views and functions

3. **Enable HTTPS**
   - Configure Let's Encrypt with Traefik
   - Generate certificates automatically
   - Configure secure redirects

4. **Add Monitoring**
   - Set up Prometheus for metrics
   - Add Grafana dashboards
   - Configure alerts

5. **Implement Backups**
   - Automated PostgreSQL backups
   - Backup storage strategy
   - Disaster recovery plan

6. **CI/CD Integration**
   - GitHub Actions or GitLab CI
   - Automated testing
   - Automated deployment

## Architecture Decisions

### Why Transaction Pooling?

pgBouncer's transaction pooling mode:
- Creates a new database connection for each transaction
- Doesn't require prepared statement changes
- Good for horizontal scaling
- Sufficient for most web applications

### Why PostgREST?

Auto-generated REST API:
- Zero boilerplate REST code
- Security via database roles and RLS
- OpenAPI/Swagger documentation
- Perfect for MVP and rapid prototyping

### Why Traefik?

- Automatic service discovery via Docker labels
- Easy hostname-based routing
- Built-in dashboard for debugging
- Production-ready reverse proxy

## Project Structure

```
PeSquel/
├── .gitignore                    # Git ignore rules
├── .gitattributes               # Git attributes for line endings
├── .env.example                 # Environment variables template
├── docker-compose.yml           # Docker Compose configuration
├── setup.sh                     # Setup automation script
├── teardown.sh                  # Teardown automation script
├── README.md                    # This file
├── traefik/
│   ├── traefik.yml             # Traefik main config
│   └── dynamic/
│       └── config.yml           # Traefik dynamic routing
├── postgres/
│   └── init/
│       ├── 01-init-db.sql      # Database initialization
│       ├── 02-create-schema.sql # API schema and tables
│       └── 03-create-roles.sql # Database roles and permissions
├── pgbouncer/
│   ├── pgbouncer.ini           # Connection pooler config
│   └── userlist.txt            # pgBouncer authentication
├── postgrest/
│   └── postgrest.conf          # PostgREST configuration
├── secrets/                    # Sensitive data (excluded from Git)
│   └── .gitkeep
├── postgres-data/              # PostgreSQL data persistence (excluded from Git)
│   └── .gitkeep
└── pgadmin-data/               # pgAdmin data persistence (excluded from Git)
    └── .gitkeep
```

## Getting Help

### Common Issues

- **Services won't start**: Check `docker compose logs -f`
- **Can't access services**: Verify hosts file entries
- **Database not initialized**: Check if `postgres-data` exists and is empty
- **Permission errors**: Check `secrets/` directory permissions

### Logs

All service logs available via:
```bash
docker compose logs [service_name] -f
```

### Docker Compose Commands

```bash
docker compose up -d       # Start services
docker compose down        # Stop services
docker compose ps          # Show status
docker compose logs -f     # Follow logs
docker compose restart     # Restart services
docker compose exec postgres psql -U pesequel_user -d pesequel_db  # Connect to database
```

## License

MIT License - Feel free to use this MVP stack for your projects!

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review service logs: `docker compose logs -f`
3. Verify hosts file entries
4. Check Docker Desktop WSL 2 backend is enabled
5. Ensure ports 80, 5432, 3000, 8080 are available

---

**Happy building with PeSequel!**
