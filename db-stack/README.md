# DB Stack - Production-Ready PostgreSQL Environment

A comprehensive PostgreSQL database stack with connection pooling, administration tools, a FastAPI todo service, and monitoring integration.

## Quick Start

1. **Environment Setup**
   ```bash
   cp .env.template .env
   # Edit .env with your passwords
   ```

2. **Start the Stack**
   ```bash
   docker compose up -d
   ```

3. **Access Services**
   - pgAdmin: http://localhost:8080 (default route)
   - Todo API: http://localhost:8080/api/ (API endpoints) 
   - API Documentation: http://localhost:8080/api/docs (Swagger UI)
   - Direct PostgreSQL: localhost:5432 (via port forwarding)
   - PgBouncer: localhost:6432

## Stack Components

- **PostgreSQL 16** with pgAudit extension
- **PgBouncer** for connection pooling
- **pgAdmin** for database administration
- **FastAPI Todo API** with CRUD operations
- **Nginx** reverse proxy (port 8080)
- **Promtail** for log shipping to Grafana Loki

## API Endpoints

The Todo API provides the following endpoints:

- `GET /health` - Health check
- `GET /todos` - List todos (with pagination)
- `POST /todos` - Create todo
- `GET /todos/{id}` - Get specific todo
- `PUT /todos/{id}` - Update todo
- `DELETE /todos/{id}` - Delete todo
- `GET /todos/search/{query}` - Search todos

## Monitoring

Logs are automatically shipped to the external Grafana stack at `grafanastack.theddt.local:3100` via Promtail, including:
- PostgreSQL audit logs
- PgBouncer connection logs
- Todo API request/response logs

## Development

See [WARP.md](WARP.md) for detailed development commands and architecture information.
