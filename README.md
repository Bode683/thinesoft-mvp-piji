# PostgreSQL pgAudit + Grafana Stack

This repository contains two separate Docker Compose stacks:

1. **DB Stack**: PostgreSQL 16 + pgAudit, PgBouncer, pgAdmin, Nginx, and Promtail
2. **Grafana Stack**: Grafana, Loki, Prometheus, Alertmanager, and K6

## Architecture

### DB Stack
- **PostgreSQL 16** with pgAudit extension (custom Dockerfile)
- **PgBouncer** as connection pooler (exposed on port 6432)
- **pgAdmin** for database management
- **Nginx** reverse proxy for HTTP routing
- **Promtail** to ship logs to Loki

### Grafana Stack
- **Grafana** for dashboards and visualization
- **Loki** for log aggregation
- **Prometheus** for metrics collection
- **Alertmanager** for alert routing
- **K6** for load testing (on-demand)

### Network Architecture
- Cross-stack communication via host networking and published ports
- Nginx proxies pgAudit dashboard traffic to Grafana
- Promtail pushes PostgreSQL logs to Loki

## Quick Start

### 1. Prerequisites
```bash
# Ensure Docker and Docker Compose are installed
docker --version
docker compose version
```

### 2. Setup Environment Files
```bash
# Copy and configure environment files
cp db-stack/.env.template db-stack/.env
cp grafana-stack/.env.template grafana-stack/.env

# Edit the .env files with your passwords
nano db-stack/.env
nano grafana-stack/.env
```

### 3. Add Hosts Entries
```bash
# Add hostname entries to /etc/hosts
sudo bash -c 'cat hosts-entries.txt >> /etc/hosts'
```

### 4. Start the Stacks
```bash
# Make scripts executable
chmod +x setup.sh teardown.sh

# Run setup script
./setup.sh
```

## Access Points

After successful setup, access these services:

- **Grafana**: http://grafanastack.theddt.local:3000
- **pgAdmin**: http://pgadmin.theddt.local
- **pgAudit Dashboard**: http://pgaudit.theddt.local (routes to Grafana)
- **Prometheus**: http://grafanastack.theddt.local:9090
- **Alertmanager**: http://grafanastack.theddt.local:9093
- **PgBouncer**: `localhost:6432` (database connections)

## Manual Operations

### Start Individual Stacks
```bash
# Start Grafana stack first
cd grafana-stack
docker compose up -d
cd ..

# Then start DB stack
cd db-stack
docker compose up -d
cd ..
```

### Stop Stacks
```bash
# Use the teardown script
./teardown.sh

# Or manually
cd db-stack && docker compose down -v && cd ..
cd grafana-stack && docker compose down -v && cd ..
```

### Run K6 Load Tests
```bash
cd grafana-stack
docker compose run --rm k6 run /scripts/example-test.js
```

### Check Logs
```bash
# PostgreSQL logs (including pgAudit)
cd db-stack && docker compose logs -f postgres

# Promtail logs
cd db-stack && docker compose logs -f promtail

# All services
docker compose logs -f  # Run in respective directories
```

## Configuration Details

### PostgreSQL + pgAudit
- Extension: `postgresql-16-pgaudit`
- Audit settings: `pgaudit.log = 'read,write,ddl,role'`
- Custom configuration in `db-stack/postgres/config/postgresql.conf`
- Initialization scripts in `db-stack/postgres/config/initdb/`

### PgBouncer
- Pool mode: `transaction`
- Max connections: `200`
- Default pool size: `20`
- Authentication: `scram-sha-256`

### Promtail → Loki
- Scrapes Docker container logs
- Filters for PostgreSQL and pgAudit events
- Pushes to Loki at `http://grafanastack.theddt.local:3100`

### Grafana Dashboards
- Pre-configured pgAudit dashboard
- Loki and Prometheus datasources auto-provisioned
- Default admin credentials from environment variables

## Troubleshooting

### Check Container Health
```bash
docker ps
docker compose ps  # In each stack directory
```

### Check Networking
```bash
# Test hostname resolution
ping grafanastack.theddt.local
curl http://grafanastack.theddt.local:3100/ready
```

### Check Logs for Errors
```bash
docker compose logs prometheus  # In grafana-stack/
docker compose logs postgres    # In db-stack/
```

### Reset Everything
```bash
./teardown.sh
docker system prune -f
./setup.sh
```

## File Structure
```
├── db-stack/
│   ├── docker-compose.yml
│   ├── .env.template
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── conf.d/
│   ├── postgres/
│   │   ├── Dockerfile
│   │   └── config/
│   ├── pgbouncer/
│   ├── pgadmin/
│   └── promtail/
├── grafana-stack/
│   ├── docker-compose.yml
│   ├── .env.template
│   ├── grafana/provisioning/
│   ├── loki/
│   ├── prometheus/
│   ├── alertmanager/
│   └── k6/scripts/
├── setup.sh
├── teardown.sh
└── hosts-entries.txt
```

## Security Notes

- Change all default passwords in `.env` files
- pgAudit logs contain sensitive information - ensure proper access controls
- This setup is intended for development/testing - additional security measures needed for production

## Extensions

### Adding Metrics Exporters
Uncomment the PostgreSQL and PgBouncer exporters in `grafana-stack/prometheus/prometheus.yml` and add the respective services to capture metrics.

### Custom Dashboards
Add JSON dashboard files to `grafana-stack/grafana/provisioning/dashboards/` for auto-provisioning.

### Email Alerts
Configure SMTP settings in `grafana-stack/alertmanager/alertmanager.yml` and environment variables.
