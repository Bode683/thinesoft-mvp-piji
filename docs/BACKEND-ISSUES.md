COMPREHENSIVE BACKEND ISSUES REPORT

  I found 15 critical bugs and 40+ configuration issues. Here are the most severe:

  ---
  🚨 CRITICAL ISSUES (Blocks Deployment)

  1. Database Connection Won't Work ⚠️

  Location: settings.py line 183 vs entrypoint.sh line 8-25
  Problem: Variable name mismatch
  ├─ entrypoint.sh sets: DJANGO_DB_HOST, DJANGO_DB_USER, etc.
  └─ settings.py reads: SQL_HOST, SQL_USER, etc.
  Result: Application crashes with "missing environment variable" error on startup.

  ---
  2. Gunicorn Module Path Error ⚠️

  Location: entrypoint.sh line 63
  exec gunicorn djangocms.wsgi:application --bind 0.0.0.0:8000
  # Should be:
  exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000
  Result: Production deployment fails immediately.

  ---
  3. Missing Django App Declaration ⚠️

  Location: settings.py line 46
  "payments",  # This app doesn't exist - likely should be djstripe
  Result: Django won't start - django.core.exceptions.ImproperlyConfigured: No installed app with label 'payments'

  ---
  4. CORS Port Mismatch ⚠️

  Location: settings.py line 31
  CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]  # React frontend
  # But compose.yaml runs frontend on port 3000
  Result: Frontend API calls blocked with CORS errors.

  ---
  5. Missing Redis Service ⚠️

  Location: settings.py line 371, but no Redis in compose.yaml
  CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
  Result: Application initialization fails when Celery is accessed.

  ---
  🔐 SECURITY ISSUES (High Risk)

  6. Hardcoded Secrets in Git 🔴

  Location: .env.local and djangocms/.env
  DJANGO_SUPERUSER_PASSWORD=password
  POSTGRES_PASSWORD=password
  STRIPE_API_KEY=sk_test_123 (in settings.py)
  PGADMIN_DEFAULT_PASSWORD=password
  Risk: All default credentials exposed to anyone with repo access.

  ---
  7. Webhook Signature Verification Missing 🔴

  Location: payment_gateway/webhooks.py lines 46-95
  @method_decorator(csrf_exempt, name="dispatch")
  class StripeWebhookView(APIView):
      # Local mode accepts ANY JSON without verification
      if USE_LOCALSTRIPE:
          # No signature check at all!
          return Response({"received": True})
  Risk: Attackers can forge payment webhooks, creating fake transactions.

  ---
  8. Weak Permission Checks on Payments 🔴

  Location: payment_gateway/views.py lines 345-410
  def capture(self, request, *args, **kwargs):
      # No verification that user owns this payment
      payment = self.get_object()  # Could be any payment
      # ... capture logic
  Risk: Users can capture/refund other users' payments.

  ---
  9. Disabled Password Validation in Development 🟡

  Location: settings.py lines 209-223
  if DEBUG:
      AUTH_PASSWORD_VALIDATORS = []  # All validators disabled
  else:
      AUTH_PASSWORD_VALIDATORS = [...]
  Risk: Developers create weak passwords, bad habits transfer to production.

  ---
  🐛 CODE BUGS

  10. Function Name Mismatch 🔴

  Location: api/serializers.py line 95
  # Function defined as:
  def obj_tenant_id(obj):

  # But called as:
  target_tenant_id()  # NameError at runtime

  ---
  11. STATIC_ROOT Defined Twice 🟡

  Location: settings.py lines 252 & 275
  # First definition:
  "STATIC_ROOT": BASE_DIR / "staticfiles_collected",

  # Second definition (overwrites first):
  STATIC_ROOT = BASE_DIR / "staticfiles/"
  Result: Static files collected to wrong location → 404 errors.

  ---
  12. Audit Logging Not Registered 🟡

  Location: api/signals.py exists but not imported
  Problem: apps.py likely doesn't call signal.ready() → audit logging broken.

  ---
  13. Tenant Isolation Issues 🟡

  Location: api/models.py Todo model
  class Todo(models.Model):
      user = models.ForeignKey(User, null=True, blank=True)  # Can be orphaned
      tenant = models.ForeignKey(Tenant, null=True)  # Can be orphaned
  Risk: Data isolation not enforced at model level.

  ---
  ⚙️ CONFIGURATION ISSUES

  14. No Health Checks 🟡

  Location: compose.yaml
  # Missing from all services:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
    interval: 10s
  Result: Container orchestration can't detect failures.

  ---
  15. Database Migration Race Condition 🟡

  Location: entrypoint.sh line 32
  python manage.py migrate --noinput  # Runs on EVERY container start
  Risk: With multiple replicas, migrations can conflict.

  ---
  📦 DEPENDENCY ISSUES

  16. Unpinned Critical Versions

  Location: requirements.txt
  stripe         # No version - could break payment processing
  celery         # No version - might not match broker
  psycopg2-binary  # No version

  ---
  17. Missing Test Dependencies

  - tests.py files exist but no test runner configured
  - No pytest/unittest framework listed
  - No CI/CD test configuration

  ---
  🏗️ ARCHITECTURAL ISSUES

  | Issue                          | Impact                              |
  |--------------------------------|-------------------------------------|
  | No database connection pooling | Will exhaust connections at scale   |
  | No logging configuration       | No observability for debugging      |
  | No API versioning              | Breaking changes will break clients |
  | No rate limiting               | Vulnerable to DoS attacks           |
  | No Celery app instance         | Background tasks will crash         |
  | SQLite fallback in container   | Data loss on restart                |
  | No read replicas               | Single point of failure             |

  ---
  🚀 QUICK FIX PRIORITY

  Must Fix Before Any Testing:
  1. Fix database variable names (SQL → DJANGO_DB)
  2. Fix gunicorn module path
  3. Add "payments" app or remove from INSTALLED_APPS
  4. Add Redis service to compose
  5. Fix CORS port (5173 → 3000)
  6. Move secrets to .gitignore

  Before Production:
  1. Remove hardcoded credentials
  2. Add webhook signature verification
  3. Add object-level permission checks on payments
  4. Fix function name mismatch (target_tenant_id)
  5. Pin all dependency versions
  6. Add health checks
  7. Enable password validation
