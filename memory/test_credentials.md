# Solomon AI — Test Credentials

## Platform Admin (God Mode)
- **Email**: admin@solomonai.us
- **Password**: Demo2026!
- **Role**: platform_admin

## Church Admin (Abundant Church)
- **Email**: shannonnieman1030@gmail.com
- **Password**: Demo2026!
- **Role**: church_admin (multi-campus access)

## Church Admin (Eden Church — Stripe POC)
- **Email**: christopher@eden-x.io
- **Password**: EdenChurch2026!
- **Role**: church_admin
- **Tenant**: eden-church-001
- **Public give URL**: /give/eden-church
- **Reset endpoint**: POST /api/admin/eden-church/reset (requires platform_admin)

## Church Member (Demo)
- **Email**: member@abundant.church
- **Password**: Demo2026!
- **Role**: member

## Stripe Test Mode (internal — never surfaced to customers)
- **Success card**: 4242 4242 4242 4242, any future expiry, any CVC, any ZIP
- **Decline card**: 4000 0000 0000 9995 (insufficient funds)
- **Test keys**: set in backend/.env as STRIPE_API_KEY / STRIPE_PUBLISHABLE_KEY (STRIPE_LIVE=true but keys are sk_test_*)
- **Brand rule**: customer-facing UI (donors, church admins, members) MUST refer to payments as "Solomon Pay". Internal platform-admin/God-Mode views may keep "Stripe" labels.

## Env-overridable test passwords
The default fallback is documented above. CI can override:
- `TEST_PASSWORD` — overrides Demo2026! for admin@solomonai.us, shannonnieman1030@gmail.com, member@abundant.church
- `TEST_EDEN_PASSWORD` / `EDEN_ADMIN_PASSWORD` — overrides EdenChurch2026! for christopher@eden-x.io
