# Keycloak REST API Documentation

## Overview

This document provides comprehensive documentation for consuming Keycloak's REST APIs for Identity and Access Management operations.

**Base URL**: `http://auth.theddt.local:8080`

**API Version**: Keycloak 23.0

---

## Table of Contents

1. [Authentication](#authentication)
2. [API Endpoints Overview](#api-endpoints-overview)
3. [Common Patterns](#common-patterns)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Best Practices](#best-practices)

---

## Authentication

### Admin API Authentication

All Admin API requests require a bearer token obtained from the token endpoint.

#### Get Admin Access Token

```http
POST /realms/master/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=password
&client_id=admin-cli
&username=admin
&password=<admin-password>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI...",
  "expires_in": 60,
  "refresh_expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI...",
  "token_type": "Bearer",
  "not-before-policy": 0,
  "session_state": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "scope": "profile email"
}
```

#### Using the Access Token

Include the access token in the Authorization header for all subsequent requests:

```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI...
```

#### Token Refresh

When the access token expires, use the refresh token to obtain a new one:

```http
POST /realms/master/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&client_id=admin-cli
&refresh_token=<refresh-token>
```

---

## API Endpoints Overview

### Base Paths

- **Admin API**: `/admin/realms/{realm}`
- **Authentication API**: `/realms/{realm}/protocol/openid-connect`
- **Account API**: `/realms/{realm}/account`

### Endpoint Categories

| Category | Base Path | Description |
|----------|-----------|-------------|
| Realms | `/admin/realms/{realm}` | Realm configuration and management |
| Users | `/admin/realms/{realm}/users` | User CRUD operations |
| Roles | `/admin/realms/{realm}/roles` | Role management |
| Clients | `/admin/realms/{realm}/clients` | Client application management |
| Groups | `/admin/realms/{realm}/groups` | Group management |
| Identity Providers | `/admin/realms/{realm}/identity-provider` | External IdP integration |
| User Federation | `/admin/realms/{realm}/components` | LDAP/AD federation |
| Sessions | `/admin/realms/{realm}/sessions` | Session management |
| Events | `/admin/realms/{realm}/events` | Audit and event logs |
| Authentication | `/realms/{realm}/protocol/openid-connect` | OAuth2/OIDC flows |

---

## Common Patterns

### Pagination

Many list endpoints support pagination:

```http
GET /admin/realms/theddt-realm/users?first=0&max=20
```

**Parameters:**
- `first`: Starting index (default: 0)
- `max`: Maximum results to return (default: 100)

### Search and Filtering

Search for resources using query parameters:

```http
GET /admin/realms/theddt-realm/users?search=john
GET /admin/realms/theddt-realm/users?username=john.doe&exact=true
GET /admin/realms/theddt-realm/users?email=john@example.com
```

### Resource Creation

POST requests typically return `201 Created` with a `Location` header:

```http
POST /admin/realms/theddt-realm/users
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "enabled": true
}
```

**Response:**
```
HTTP/1.1 201 Created
Location: http://auth.theddt.local:8080/admin/realms/theddt-realm/users/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

Extract the resource ID from the Location header.

### Resource Updates

PUT requests for updates return `204 No Content`:

```http
PUT /admin/realms/theddt-realm/users/{user-id}
Content-Type: application/json

{
  "firstName": "John",
  "lastName": "Doe",
  "email": "john.doe@example.com"
}
```

**Response:**
```
HTTP/1.1 204 No Content
```

### Resource Deletion

DELETE requests return `204 No Content`:

```http
DELETE /admin/realms/theddt-realm/users/{user-id}
```

**Response:**
```
HTTP/1.1 204 No Content
```

---

## Error Handling

### HTTP Status Codes

| Status Code | Meaning | Description |
|-------------|---------|-------------|
| 200 | OK | Request successful, response body included |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request successful, no response body |
| 400 | Bad Request | Invalid request parameters or body |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "error": "invalid_grant",
  "error_description": "Invalid user credentials"
}
```

Or for Admin API:

```json
{
  "errorMessage": "User exists with same username"
}
```

### Common Errors

#### 401 Unauthorized
- **Cause**: Expired or invalid access token
- **Solution**: Obtain a new access token using refresh token or re-authenticate

#### 403 Forbidden
- **Cause**: Insufficient permissions for the operation
- **Solution**: Ensure the authenticated user has the required realm or client roles

#### 409 Conflict
- **Cause**: Resource already exists (e.g., duplicate username)
- **Solution**: Use a unique identifier or update the existing resource

---

## Rate Limiting

Keycloak does not implement built-in rate limiting at the API level. Consider implementing:

1. **Application-level rate limiting** in your client application
2. **Reverse proxy rate limiting** using Nginx, Kong, or API Gateway
3. **Brute force protection** (enabled in realm settings) for authentication endpoints

---

## Best Practices

### 1. Token Management

- **Cache tokens**: Store access tokens and reuse until expiration
- **Refresh proactively**: Refresh tokens before they expire
- **Secure storage**: Store tokens securely (encrypted storage, secure cookies)
- **Token revocation**: Revoke tokens on logout

### 2. Error Handling

- **Implement retry logic**: For transient errors (500, 503)
- **Handle token expiration**: Automatically refresh and retry
- **Log errors**: Log API errors for debugging and monitoring
- **User-friendly messages**: Don't expose technical errors to end users

### 3. Performance Optimization

- **Use pagination**: Always paginate large result sets
- **Minimize requests**: Batch operations when possible
- **Cache responses**: Cache static data (roles, clients) with appropriate TTL
- **Use search parameters**: Filter server-side instead of client-side

### 4. Security

- **HTTPS only**: Always use HTTPS in production
- **Validate input**: Validate all input data before sending to API
- **Least privilege**: Use service accounts with minimal required permissions
- **Audit logging**: Enable and monitor admin events

### 5. API Versioning

- **Monitor deprecations**: Check Keycloak release notes for API changes
- **Test upgrades**: Test API compatibility before upgrading Keycloak
- **Use stable endpoints**: Prefer stable, documented endpoints

---

## API Examples

### User Management

#### Create User
```bash
curl -X POST "http://auth.theddt.local:8080/admin/realms/theddt-realm/users" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "email": "john.doe@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "enabled": true,
    "emailVerified": true,
    "credentials": [{
      "type": "password",
      "value": "SecurePass123!",
      "temporary": false
    }]
  }'
```

#### Get User by ID
```bash
curl -X GET "http://auth.theddt.local:8080/admin/realms/theddt-realm/users/${USER_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

#### Update User
```bash
curl -X PUT "http://auth.theddt.local:8080/admin/realms/theddt-realm/users/${USER_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John Updated",
    "lastName": "Doe Updated"
  }'
```

#### Delete User
```bash
curl -X DELETE "http://auth.theddt.local:8080/admin/realms/theddt-realm/users/${USER_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Role Management

#### Assign Role to User
```bash
curl -X POST "http://auth.theddt.local:8080/admin/realms/theddt-realm/users/${USER_ID}/role-mappings/realm" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '[{
    "id": "${ROLE_ID}",
    "name": "developer"
  }]'
```

### Authentication Flows

#### Password Grant (Direct Access)
```bash
curl -X POST "http://auth.theddt.local:8080/realms/theddt-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=web-app" \
  -d "username=john.doe" \
  -d "password=SecurePass123!" \
  -d "scope=openid profile email"
```

#### Client Credentials Grant
```bash
curl -X POST "http://auth.theddt.local:8080/realms/theddt-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=service-account" \
  -d "client_secret=${CLIENT_SECRET}"
```

### LDAP Federation

#### Create LDAP Provider
```bash
curl -X POST "http://auth.theddt.local:8080/admin/realms/theddt-realm/components" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "openldap-federation",
    "providerId": "ldap",
    "providerType": "org.keycloak.storage.UserStorageProvider",
    "config": {
      "enabled": ["true"],
      "priority": ["0"],
      "editMode": ["READ_ONLY"],
      "vendor": ["other"],
      "usernameLDAPAttribute": ["uid"],
      "rdnLDAPAttribute": ["uid"],
      "uuidLDAPAttribute": ["entryUUID"],
      "userObjectClasses": ["inetOrgPerson, organizationalPerson"],
      "connectionUrl": ["ldap://openldap:389"],
      "usersDn": ["ou=People,dc=theddt,dc=local"],
      "authType": ["simple"],
      "bindDn": ["cn=admin,dc=theddt,dc=local"],
      "bindCredential": ["admin123"]
    }
  }'
```

#### Sync LDAP Users
```bash
curl -X POST "http://auth.theddt.local:8080/admin/realms/theddt-realm/user-storage/${PROVIDER_ID}/sync?action=triggerFullSync" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## Additional Resources

- **Keycloak Admin REST API Documentation**: https://www.keycloak.org/docs-api/23.0/rest-api/
- **Keycloak Server Administration Guide**: https://www.keycloak.org/docs/latest/server_admin/
- **OAuth 2.0 RFC**: https://tools.ietf.org/html/rfc6749
- **OpenID Connect Specification**: https://openid.net/specs/openid-connect-core-1_0.html

---

## Support

For issues or questions:
1. Check Keycloak logs: `docker logs iam-keycloak`
2. Review Keycloak documentation
3. Check Keycloak community forums
4. Review the implementation plan in `docs/IMPLEMENTATION_PLAN.md`
