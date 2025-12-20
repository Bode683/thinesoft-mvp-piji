# PKaKey — Functional Specification Document (MVP)

**Project:** PKaKey (Thinesoft PKI Platform)  
**Version:** MVP 1.0  
**Date:** 2025-12-19  
**Author:** Bodelain / Thinesoft Architecture Team

---

## 1. Purpose

The purpose of this document is to define the functional requirements, system behavior, and architecture of the PKaKey MVP — a secure, multi-tenant Public Key Infrastructure (PKI) platform for AppFabrik. This document serves as a blueprint for developers and DevOps teams to implement, test, and deploy the system.

---

## 2. Scope

The MVP delivers:

- Certificate issuance and revocation
- SCEP enrollment for devices
- OCSP status validation
- EAP-TLS integration with FreeRADIUS
- Operator back-office (Wagtail)
- Health check and key rotation workflows
- CI/CD deployment pipeline
- Observability and alerting

---

## 3. System Overview

### 3.1 Architecture Layers

| Layer             | Description |
|------------------|-------------|
| **Ingress**       | Traefik reverse proxy with TLS/mTLS routing |
| **Identity**      | Keycloak for OIDC authentication and RBAC |
| **Application**   | Django REST API (PkaKey), Wagtail CMS, ViewFlow workflows |
| **Crypto Engine** | CSR validation, certificate signing, PKCS#7 packaging |
| **Services**      | OCSP responder, SCEP proxy |
| **Data**          | PostgreSQL (persistent), Redis (broker/cache), Volumes |
| **Integration**   | FreeRADIUS (EAP-TLS), APISIX + LibreTranslate |
| **CI/CD**         | GitLab CI, Helm/Compose deploy, container registry |
| **Monitoring**    | Prometheus, Grafana, SIEM, Slack/Email alerts |

---

## 4. Functional Requirements

### 4.1 Certificate Lifecycle

- ✅ Issue certificate from CSR (API)
- ✅ Revoke certificate (API or UI)
- ✅ Query certificate status (OCSP)
- ✅ Store certificate metadata in DB
- ✅ Support PKCS#7 and PEM formats

### 4.2 SCEP Enrollment

- ✅ Accept PKIOperation (SCEP)
- ✅ Validate challenge password (optional)
- ✅ Return PKCS#7 signed cert
- ✅ Log enrollment attempts

### 4.3 OCSP Responder

- ✅ Accept DER OCSP requests
- ✅ Query certificate status via API
- ✅ Cache responses per serial
- ✅ Admin endpoint to purge cache

### 4.4 Workflows

- ✅ HealthCheckFlow: detect expired/expiring certs
- ✅ KeyRotationFlow: intermediate/OCSP key rotation
- ✅ Slack/Email/SIEM alerts on workflow events

### 4.5 Back-Office (Wagtail)

- ✅ Dashboard: certificate health
- ✅ Actions: issue, revoke, rotate
- ✅ View workflow instances
- ✅ Role-based access via Keycloak

### 4.6 Authentication & Authorization

- ✅ OIDC login via Keycloak
- ✅ JWT validation for API
- ✅ Role-based access control (admin, operator)

### 4.7 EAP-TLS Integration

- ✅ FreeRADIUS validates client certs
- ✅ OCSP responder checks revocation
- ✅ Accept/reject based on OCSP status

---

## 5. Non-Functional Requirements

- 🔐 TLS/mTLS for all services
- 📈 Prometheus metrics for all components
- 📄 Audit logging for all admin actions
- 🔁 Horizontal scalability (stateless services)
- 🧪 CI/CD pipeline with test stages
- 🧩 Modular deployment (Docker Compose, Helm)

---

## 6. API Endpoints (MVP)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/pki/scep-enroll/` | Accept CSR via SCEP |
| GET    | `/api/pki/certificates/{serial}/status/` | Return cert status |
| POST   | `/api/pki/certificates/{serial}/revoke/` | Revoke certificate |
| GET    | `/api/pki/certificates/` | List issued certs |
| POST   | `/api/pki/workflows/health-check/` | Trigger health check |
| POST   | `/api/pki/workflows/key-rotation/` | Start key rotation |

---

## 7. Data Model (Simplified)

### CertificateRecord

- `serial`: string
- `subject`: string
- `issued_at`: datetime
- `expires_at`: datetime
- `revoked`: boolean
- `revoked_at`: datetime
- `csr_pem`: text
- `cert_pem`: text
- `tenant`: string

### HealthCheckProcess

- `started_at`: datetime
- `expired_serials`: list
- `expiring_serials`: list
- `alerts_sent`: boolean

---

## 8. Deployment Environments

| Env     | Description |
|---------|-------------|
| DEV     | docker-compose, self-signed certs |
| QUALIF  | staging, intermediate_v2 available |
| PROD    | HA, HSM/Vault, SIEM, alerting |

---

## 9. CI/CD Pipeline

- ✅ Lint, unit, integration tests
- ✅ Security scans (SAST, deps)
- ✅ Build/push Docker images
- ✅ Deploy to DEV → QUALIF → PROD
- ✅ Manual approval for PROD

---

## 10. Monitoring & Alerts

- Prometheus metrics: PkaKey, OCSP, Traefik, FreeRADIUS
- Grafana dashboards: cert issuance, OCSP latency, queue depth
- SIEM logs: audit trails, revocations
- Alerts: Slack, Email, SIEM triggers

---

## 11. Architecture Diagram

See `pkaKey-architecture.puml` (PlantUML) for full system layout including layers and planes.

---

## 12. Glossary

- **CSR**: Certificate Signing Request
- **OCSP**: Online Certificate Status Protocol
- **SCEP**: Simple Certificate Enrollment Protocol
- **EAP-TLS**: Extensible Authentication Protocol - Transport Layer Security
- **RBAC**: Role-Based Access Control
- **HSM**: Hardware Security Module

---

## 13. Appendix

- PlantUML diagrams (architecture, workflows)
- OpenSSL scripts for CA bootstrap
- Docker Compose and Helm charts
- Test plan and coverage report

