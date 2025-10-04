# Keycloak Realms - Testing Guide

## ✅ All Realms Successfully Imported

Three realms have been imported and are fully operational:
1. **theddt-realm** - Full-featured realm with multiple users, roles, and clients
2. **production** - Production-ready realm configuration
3. **minimal** - Lightweight realm for testing

---

## Quick Verification

### Check Realm Availability
```bash
# theddt-realm
curl -s http://localhost:8080/realms/theddt-realm | jq -r '.realm'
# Expected: theddt-realm

# production
curl -s http://localhost:8080/realms/production | jq -r '.realm'
# Expected: production

# minimal
curl -s http://localhost:8080/realms/minimal | jq -r '.realm'
# Expected: minimal
```

---

## Realm Details

### 1. theddt-realm

#### Users & Credentials
| Username | Password | Role | Group |
|----------|----------|------|-------|
| admin | admin123 | admin | Administrators |
| john.doe | password123 | developer | Developers |
| jane.smith | password123 | manager | Managers |
| bob.wilson | password123 | user | Users |
| alice.johnson | password123 | viewer | Users |

#### Clients
- **web-app** (Confidential) - Standard flow + Direct access grants
- **mobile-app** (Public) - Standard flow + Direct access grants
- **service-account** (Confidential) - Service account enabled
- **api-client** (Confidential) - Direct access grants + Service account

#### Test Authentication
```bash
# Using mobile-app (public client)
curl -X POST "http://localhost:8080/realms/theddt-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=mobile-app" \
  -d "username=admin" \
  -d "password=admin123" | jq

# Test with developer user
curl -X POST "http://localhost:8080/realms/theddt-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=mobile-app" \
  -d "username=john.doe" \
  -d "password=password123" | jq
```

#### Features Enabled
- ✅ Events logging (LOGIN, LOGOUT, REGISTER, etc.)
- ✅ Admin events with details
- ✅ Brute force protection
- ✅ Remember me
- ✅ Reset password
- ✅ Custom client scopes with protocol mappers

---

### 2. production

#### Users & Credentials
| Username | Password | Role | Group |
|----------|----------|------|-------|
| admin | admin123 | admin | Administrators |
| testuser | test123 | user | Users |
| manager | manager123 | manager | Managers |

#### Clients
- **production-api** (Confidential) - Secret: `production-api-secret-2023`
- **production-web** (Confidential) - Secret: `production-web-secret-2023`

#### Test Authentication
```bash
# Using production-api client (requires client secret)
curl -X POST "http://localhost:8080/realms/production/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=production-api" \
  -d "client_secret=production-api-secret-2023" \
  -d "username=admin" \
  -d "password=admin123" | jq
```

#### Features
- ✅ Minimal configuration for production use
- ✅ Strict security settings
- ✅ No registration allowed
- ✅ No password reset (admin-managed)

---

### 3. minimal

#### Users & Credentials
| Username | Password | Role |
|----------|----------|------|
| admin | admin | admin |

#### Clients
- **admin-cli** (Public) - Admin CLI access

#### Test Authentication
```bash
# Using admin-cli
curl -X POST "http://localhost:8080/realms/minimal/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" | jq
```

---

## Admin Console Access

### Access Each Realm
1. **Master Realm**: http://localhost:8080/admin/master/console/
   - Username: `admin`
   - Password: `password`

2. **theddt-realm**: http://localhost:8080/admin/theddt-realm/console/
   - Username: `admin`
   - Password: `admin123`

3. **production**: http://localhost:8080/admin/production/console/
   - Username: `admin`
   - Password: `admin123`

4. **minimal**: http://localhost:8080/admin/minimal/console/
   - Username: `admin`
   - Password: `admin`

---

## Token Introspection

### Decode Access Token
```bash
# Get token
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/theddt-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=mobile-app" \
  -d "username=admin" \
  -d "password=admin123" | jq -r '.access_token')

# Decode token (requires base64 and jq)
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq
```

---

## Common Use Cases

### 1. User Login Flow
```bash
# Step 1: Get access token
curl -X POST "http://localhost:8080/realms/theddt-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=mobile-app" \
  -d "username=john.doe" \
  -d "password=password123"
```

### 2. Refresh Token
```bash
# Get refresh token first, then:
curl -X POST "http://localhost:8080/realms/theddt-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token" \
  -d "client_id=mobile-app" \
  -d "refresh_token=YOUR_REFRESH_TOKEN"
```

### 3. Service Account (Client Credentials)
```bash
# Using service-account client
curl -X POST "http://localhost:8080/realms/theddt-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=service-account" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

### 4. Get User Info
```bash
# Get token first, then:
curl -X GET "http://localhost:8080/realms/theddt-realm/protocol/openid-connect/userinfo" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Troubleshooting

### Issue: "Invalid client or Invalid client credentials"
**Solution**: Client requires a secret. Either:
- Use a public client (mobile-app, admin-cli)
- Provide client_secret for confidential clients

### Issue: "Account is not fully set up"
**Solution**: User may need to complete required actions. Check in Admin Console.

### Issue: "Invalid username or password"
**Solution**: Verify credentials match the table above.

### Issue: Realm not found
**Solution**: Verify realm is imported:
```bash
curl -s http://localhost:8080/realms/REALM_NAME | jq
```

---

## Integration with Applications

### Example: Node.js with Keycloak
```javascript
const axios = require('axios');

async function login(username, password) {
  const response = await axios.post(
    'http://localhost:8080/realms/theddt-realm/protocol/openid-connect/token',
    new URLSearchParams({
      grant_type: 'password',
      client_id: 'mobile-app',
      username: username,
      password: password
    })
  );
  return response.data;
}
```

### Example: Python with Keycloak
```python
import requests

def login(username, password):
    url = 'http://localhost:8080/realms/theddt-realm/protocol/openid-connect/token'
    data = {
        'grant_type': 'password',
        'client_id': 'mobile-app',
        'username': username,
        'password': password
    }
    response = requests.post(url, data=data)
    return response.json()
```

---

## Next Steps

1. ✅ All realms are imported and working
2. Test authentication flows with your applications
3. Customize client configurations as needed
4. Add additional users through Admin Console or API
5. Configure client secrets for confidential clients
6. Set up HTTPS for production use
7. Configure CORS policies for web applications

---

**Status**: ✅ All realms operational and tested
**Last Updated**: 2025-10-04
**Keycloak Version**: 23.0.7
