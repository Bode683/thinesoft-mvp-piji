# Payment Gateway (Stripe V3) — Developer Guide

This document explains how the `payment_gateway` feature works, how to configure environments, API endpoints, webhooks, and how to test both production (Stripe Checkout) and local (localstripe) flows for both one-off payments and subscriptions.

- Code location: `payment_gateway/`
- Models: `payment_gateway/models.py`
- Views: `payment_gateway/views.py`
- Webhooks: `payment_gateway/webhooks.py`
- URLs: `payment_gateway/urls.py`
- Settings: `backend/settings.py`
 - Subscriptions seeder: `payment_gateway/management/commands/seed_subscriptions.py`

## Overview

The gateway supports Stripe V3 via `django-payments` for one-off payments and the Stripe Python SDK for subscriptions.

- Production flow uses Stripe Checkout Sessions (hosted payment page).
- Local development uses PaymentIntents against a local, stateful Stripe mock (localstripe). Localstripe does not support Checkout Sessions, hence a different flow is used locally.
- Subscriptions in local mode use legacy Stripe "Plans" (not "Prices"). In production, subscriptions use modern Prices.

Key decisions:

- Webhook signature verification is ON in production and OFF in local.
- In local mode, the server creates and auto-confirms a PaymentIntent to simulate successful payments quickly.
- Metadata is attached to the PaymentIntent so webhook processing can locate the corresponding `Payment` record.
 - For subscriptions in local mode: we create legacy Plans and subscribe using `items=[{"plan": plan_id}]`. In production: we subscribe using Prices with `items=[{"price": price_id}]`.

## Environment configuration

Relevant environment variables (load order: `.env.local` then `.env` in `backend/settings.py`):

- USE_LOCALSTRIPE: `True|False` — toggles local vs prod behavior.
- STRIPE_API_KEY: Set for production. In local, a dummy key is used: `sk_test_123`.
- STRIPE_WEBHOOK_SECRET: Set for production. In local, a dummy secret is used: `whsec_123`.
- LOCALSTRIPE_URL: Base URL for localstripe (default `http://127.0.0.1:8420`).
- PAYMENT_HOST: Host used to construct success/failure URLs (e.g., `localhost:8000`).
- PAYMENT_USES_SSL: `True|False` whether to use HTTPS for success/failure URLs.
- STRIPE_API_VERSION: Optional. Pin a Stripe API version (e.g., `2020-08-27`) if needed.

Additional Django dev tips:

- SECURE_SSL_REDIRECT: set to `False` locally to avoid redirecting webhook HTTP to HTTPS.
- ALLOWED_HOSTS: include any hostname/IP used by webhooks to reach Django.

## Settings behavior (summary)

See `backend/settings.py`:

- When `USE_LOCALSTRIPE=True`:
  - `stripe.api_base`, `stripe.uploads_base`, `stripe.files_base` point to `LOCALSTRIPE_URL`.
  - `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET` use dummy values.
  - `PAYMENT_VARIANTS['stripe']` is set with `secure_endpoint=False` (no signature verification).
- When `USE_LOCALSTRIPE=False`:
  - Real Stripe keys from env.
  - `PAYMENT_VARIANTS['stripe']` has `secure_endpoint=True` (signature verified).

`PAYMENT_MODEL` is set to `payment_gateway.Payment`.

## Models summary

- `Payment` (extends `django-payments` `BasePayment`): stores pricing, user, gateway, token, attrs, transaction_id, etc.
- `PaymentGatewayConfig`: stores active gateways and their variants.
- `PaymentLog`: audit trail of relevant events per payment.

See `payment_gateway/models.py` for details on fields and helper methods (success/failure URL generation reads `PAYMENT_HOST`/`PAYMENT_USES_SSL`).

## API Endpoints

Router base: `payment_gateway/urls.py`

- `GET /api/v1/gateways/` — list active gateways.
- `GET /api/v1/payments/` — list user payments.
- `POST /api/v1/payments/create_payment/` — create a new payment.
- `POST /api/v1/payments/{id}/capture_payment/` — capture a preauthorized payment.
- `POST /api/v1/payments/{id}/refund_payment/` — refund a confirmed payment.
- `GET /api/v1/payments/{id}/logs/` — fetch payment logs.
- `GET /api/v1/payments/{id}/success/` — success redirect landing (for Checkout).
- `GET /api/v1/payments/{id}/failure/` — failure/cancel redirect landing (for Checkout).
- `POST /api/v1/webhooks/stripe/` — Stripe webhooks (variant=`stripe`).

### Subscriptions

- `GET /api/v1/subscriptions/plans/` — list available plans with active pricing options.
- `POST /api/v1/subscriptions/subscribe/` — body: `{ "plan_id": <int> }` — create a subscription for the current user.
- `POST /api/v1/subscriptions/cancel/` — body: `{ "subscription_id": "sub_..." }` — cancel at period end.
- `GET /api/v1/subscriptions/status/` — list user subscriptions and mapped plan metadata.
- `GET /api/v1/subscriptions/me/limits/` — resolves today’s usage limits from the active plan (or default plan).

### Create Payment behavior (one-off)

`payment_gateway/views.py:PaymentViewSet.create_payment()`

- Production (`USE_LOCALSTRIPE=False`):

  - Delegates to `django-payments` Stripe provider via `payment.get_form()`.
  - Catches `RedirectNeeded` to return `gateway_url` (Stripe Checkout Session URL).

- Local (`USE_LOCALSTRIPE=True`):
  - Creates a PaymentIntent using the Stripe Python SDK with:
    - amount: converted to the smallest currency unit via `StripeProviderV3.convert_amount()`.
    - currency: lowercase ISO code.
    - confirm=True and a test method `pm_card_visa` (auto-confirm flow for convenience).
    - metadata: `{ payment_id: <Payment.id>, token: <Payment.token> }`.
  - Sets `payment.transaction_id = intent.id` and `payment.attrs.intent = intent`.
  - Sets `Payment.status` based on PI status (`succeeded`→`confirmed`, `requires_capture`→`preauth`, else `waiting`).
  - Returns `201` with `payment_id`, `status`, `intent_id`, `client_secret` (if present), `amount`, `currency`.

### Capture and Refund

- Capture (`capture_payment`):

  - Uses `payment.capture()` from `django-payments` when status is `preauth`.
  - In local mode, if you plan to test manual capture, adjust creation to use `capture_method="manual"` and implement a direct PI capture call (`stripe.PaymentIntent.capture`). Currently not required for auto-confirm flow.

- Refund (`refund_payment`):
  - Uses `payment.refund()`; in local mode you can switch to direct PI-based refunds if needed: `stripe.Refund.create(payment_intent=pi_id, amount=...)`.

## Webhooks

Route: `POST /api/v1/webhooks/stripe/` (see `payment_gateway/urls.py`)

- Production mode:

  - Uses `StripeProviderV3` to verify signatures and process events (e.g., Checkout Session completion updating payment status). See `payment_gateway/webhooks.py` provider branch.

- Local mode:
  - Signature verification is disabled.
  - Parses JSON and handles PaymentIntent events:
    - `payment_intent.succeeded` → set `PaymentStatus.CONFIRMED`.
    - `payment_intent.payment_failed` → set `PaymentStatus.ERROR`.
    - `payment_intent.canceled` → set `PaymentStatus.REJECTED`.
  - Locates `Payment` via `event.data.object.metadata.payment_id`.
  - Stores latest intent payload in `payment.attrs.intent`.

Note: In our default local flow we auto-confirm the PaymentIntent, so webhooks are optional to achieve a confirmed status.

### localstripe webhook configuration

localstripe does not support creating webhook endpoints via the Stripe API; instead, use its special `_config` route to register a forward URL that it will POST to.

- If localstripe runs on your host: `http://localhost:8420`
- If it runs in Docker, ensure it can reach Django. Recommended URLs from the container:
  - `http://172.17.0.1:8000/api/v1/webhooks/stripe/` (Linux Docker bridge IP)
  - or `http://host.docker.internal:8000/api/v1/webhooks/stripe/` (with `extra_hosts: ["host.docker.internal:host-gateway"]`)

Register the webhook (form-encoded minimal):

```bash
curl -X POST http://localhost:8420/_config/webhooks/django \
  -d url=http://172.17.0.1:8000/api/v1/webhooks/stripe/ \
  -d secret=whsec_local
```

Optionally specify events (JSON):

```bash
curl -X POST http://localhost:8420/_config/webhooks/django \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://172.17.0.1:8000/api/v1/webhooks/stripe/",
    "secret": "whsec_local",
    "events": [
      "product.created",
      "plan.created",
      "customer.created",
      "customer.updated",
      "customer.deleted",
      "customer.source.created",
      "customer.subscription.created",
      "customer.subscription.deleted",
      "invoice.created",
      "invoice.payment_succeeded",
      "invoice.payment_failed"
    ]
  }'
```

Troubleshooting:
- 400 from `_config`: try the minimal form-encoded variant without events.
- 404 to your Django URL from container: ensure Django listens on `0.0.0.0:8000`, and `ALLOWED_HOSTS` includes the host you use.

## Testing the flows

### Prerequisites

- Localstripe running at `LOCALSTRIPE_URL` (default `http://127.0.0.1:8420`).
- Django running and accessible to you (and optionally to localstripe if you want (mock) webhooks delivered).

### Local (PaymentIntents) — Create a payment

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/payments/create_payment/ \
  -H "Authorization: Token <YOUR_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "gateway": "Stripe",
    "description": "Local PI Test",
    "amount": "10.00",
    "currency": "USD",
    "order_id": "ord_123",
    "metadata": {"note": "local test"}
  }'
```

Expected response snippet (201):

```json
{
  "payment_id": 42,
  "status": "confirmed",
  "intent_id": "pi_123",
  "client_secret": "...", // may be present
  "amount": "10.00",
  "currency": "USD"
}
```

### Local webhooks (optional)

Localstripe must be able to reach Django inside your network:

- Run Django bound to `0.0.0.0` and expose `8000`.
- Use a URL reachable from the localstripe container (e.g., `http://django:8000` in docker-compose or the host bridge IP such as `http://172.17.0.1:8000`).
- Add that host to `ALLOWED_HOSTS` in `backend/settings.py`.

Register the webhook using `_config` as shown above.

### Production (Stripe Checkout) — Create a payment

Same endpoint as local, different behavior under the hood:

- The response includes `gateway_url` to redirect users to Stripe Checkout.
- Webhook signature is verified by `StripeProviderV3`.

Example response snippet (201):

```json
{
  "payment_id": 99,
  "status": "waiting",
  "gateway_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "amount": "25.00",
  "currency": "USD"
}
```

## Subscriptions: seeding and local-vs-prod behavior

### Seeding plans and pricing

We provide a management command to seed three plans and their Stripe counterparts:

- Day Pass: $5/day, non-renewing
- Premium: $200/month, auto-renewing
- Free: $0/month, default, limits: 180 minutes/day and 300 MB/day

Command:

```bash
python manage.py seed_subscriptions --day_pass_amount 5 --premium_amount 200 --free_amount 0
```

Behavior:
- Local (`USE_LOCALSTRIPE=True`):
  - Creates Stripe Products and legacy Plans (not Prices). Stores the legacy plan ID in `PlanPricing.stripe_price_id` for compatibility.
  - Subscribes using `items=[{"plan": <plan_id>}]`.
- Production (`USE_LOCALSTRIPE=False`):
  - Creates Stripe Products and modern Prices. Stores Price IDs in `PlanPricing.stripe_price_id`.
  - Subscribes using `items=[{"price": <price_id>}]`.

### Subscription endpoints quick test

```bash
# List plans
curl -H "Authorization: Token <TOKEN>" http://localhost:8000/api/v1/subscriptions/plans/

# Subscribe to a plan
curl -X POST -H "Authorization: Token <TOKEN>" -H "Content-Type: application/json" \
  -d '{"plan_id": 1}' http://localhost:8000/api/v1/subscriptions/subscribe/

# Status
curl -H "Authorization: Token <TOKEN>" http://localhost:8000/api/v1/subscriptions/status/

# Cancel at period end
curl -X POST -H "Authorization: Token <TOKEN>" -H "Content-Type: application/json" \
  -d '{"subscription_id": "sub_..."}' http://localhost:8000/api/v1/subscriptions/cancel/

# Usage limits for current user
curl -H "Authorization: Token <TOKEN>" http://localhost:8000/api/v1/subscriptions/me/limits/
```

## Payment & Subscription Workflows

### One-off Payments (Local)
- Client calls `POST /api/v1/payments/create_payment/`.
- Server creates a PaymentIntent on localstripe and auto-confirms it with `pm_card_visa`.
- Optional webhooks via `_config` forward to `/api/v1/webhooks/stripe/` and update logs/status.

### One-off Payments (Production)
- Client calls same endpoint.
- Server creates a Stripe Checkout Session via `django-payments` and returns `gateway_url`.
- User completes Checkout on Stripe; dj-payments webhook validates signature and updates status.

### Subscriptions (Local)
- Seed Products + legacy Plans with `seed_subscriptions`.
- Client calls `POST /api/v1/subscriptions/subscribe/ { plan_id }`.
- Server ensures a Stripe Customer exists and subscribes using `items=[{"plan": ...}]`.
- For non-auto-renew plans (Day Pass), we set `cancel_at_period_end=True`.
- Webhooks (from localstripe `_config`) can deliver `product.created`, `plan.created`, `customer.subscription.created`, invoices, etc.

### Subscriptions (Production)
- Same flow, but subscriptions use Prices: `items=[{"price": ...}]`.
- You can enable dj-stripe’s own webhook endpoint if desired; otherwise, you may continue to handle events in your custom webhook as needed.

## Troubleshooting

- 404 on `/v1/checkout/sessions` in local: localstripe does not support Checkout Sessions. Use local PaymentIntent flow.
- Webhook delivery from localstripe fails to `localhost:8000`: the container cannot reach your host via `localhost`. Use a docker network host (service name) or host bridge IP and update `ALLOWED_HOSTS`.
- "No API key provided": ensure `STRIPE_API_KEY` is set (prod) or `USE_LOCALSTRIPE=True` (local) so dummy key is used.
- Amount conversion errors: amounts are converted with `StripeProviderV3.convert_amount(currency, amount_decimal)`; ensure currency codes are valid.
 - localstripe 404 on `/v1/prices`: use legacy Plans in local mode (handled by the seeding command and subscribe flow).

## Extending

- To test manual capture locally:
  - Create PI with `capture_method="manual"`.
  - Implement `POST /api/v1/payments/{id}/capture_intent/` calling `stripe.PaymentIntent.capture(pi_id, amount_to_capture)`.
- To test direct refunds locally:
  - Implement a PI-specific refund path using `stripe.Refund.create(payment_intent=pi_id, amount=...)` and update `Payment` status/logs.

## Security notes

- Production webhooks require signature verification and use real secrets.
- Do not expose local dummy keys in production.
- Keep `SECURE_SSL_REDIRECT=True` in production.

## TODO status

[completed] Pivot to PaymentIntents for localstripe and update webhook handling.
[pending] Add PI-specific confirm/capture/refund endpoints if needed.
[pending] Update test suite for local mode.
[pending] Use django-configurations to simplify managing different environments (development, staging, production).
[pending] Use drf-spectacular for API Schema and Documentation
[pending] Implement PayPal Webhooks: The handle_paypal_webhook and process_paypal_event methods are placeholders.

## References

- `payments` (django-payments): `payments/stripe/providers.py` — `StripeProviderV3`
- Stripe Python SDK: https://github.com/stripe/stripe-python
- localstripe: https://pypi.org/project/localstripe/
