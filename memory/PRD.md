# Solomon AI — Church Management Platform PRD

## Product Overview
Multi-tenant SaaS Church Management System. React + FastAPI + MongoDB. Multi-campus organizations supported. Admin/Member toggle (Lyft dual-mode). Full platform admin user management with role promotions.

## Accounts (All password: Demo2026!)
| Name | Email | Role | Access |
|------|-------|------|--------|
| Platform Admin | admin@solomonai.us | Platform Admin | All churches, create users, promote roles |
| Shannon Nieman | shannonnieman1030@gmail.com | Lead Pastor (38 perms) | East, Downtown, West (God Mode) |
| Jacob Pacheco | jacobpacheco@abundanteast.com | Pastoral Staff (38 perms) | East, Downtown, West (God Mode) |
| Aivy Vopham | avopham@gmail.com | Church Admin | East, Downtown, West |

## Key Platform Features
- **Create User**: Platform admin creates accounts tied to specific churches (9 role templates)
- **Promote to Admin**: Platform admin changes any member's role → user gets admin toggle on next login
- **Multi-Campus**: Campus switcher for org-level admins (Abundant: East, Downtown, West)
- **Admin/Member Toggle**: Users with admin permissions can switch between admin and member views
- **Church Isolation**: Church admins cannot see other churches or platform-level data

## Demo Data
- Abundant East: 22K members, A+ (100) health score
- Abundant Downtown: 18.5K members, A+ (100)
- Abundant West: 14K members, A+ (100)
- Non-Abundant: F scores (20-31) for pitch contrast

## Phase A: Planning Center Competitor (IN PROGRESS)
Backend routes done. Frontend pages NOT YET built:
- Services/Worship Planning, Volunteer Scheduling, Households
- Member Directory, Pricing Page, Branding Settings

## Backlog
- P0: Phase A frontend pages
- P2: Real Stripe/Pushpay integration
- P2: server.py modular refactor (~15k lines)
- P3: React Native mobile app
