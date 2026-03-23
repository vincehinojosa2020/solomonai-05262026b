# Solomon AI — Church Management Platform PRD

## Product Overview
Multi-tenant SaaS Church Management System. React + FastAPI + MongoDB. Multi-campus organizations supported with campus switcher. Admin ↔ Member toggle (Lyft dual-mode) for all users with admin permissions.

## Test Accounts (All password: Demo2026!)
| Name | Email | Role | Toggle | Campus |
|------|-------|------|--------|--------|
| Platform Admin | admin@solomon.ai | Platform Admin | Admin only | All |
| Shannon Nieman | shannonnieman1030@gmail.com | Lead Pastor (38 perms, God Mode) | Admin ↔ Member | East, Downtown, West |
| Aivy Vopham | avopham@gmail.com | Church Admin (33 perms) | Admin ↔ Member | East, Downtown, West |
| Jay Pacheco | jacobpacheco@live.com | Small Group Leader (18 perms) | Admin ↔ Member | East |
| Jacob Pacheco | jacobpacheco@abundanteast.com | Member (11 perms) | Member only | East |
| Vince Hinojosa | vince@charlottesoftwareengineering.com | Member | Member only | East |

## Demo Data
- Abundant East: 22K members, A+ (100) health score
- Abundant Downtown: 18.5K members, A+ (100) health score
- Abundant West: 14K members, A+ (100) health score
- Non-Abundant churches: F scores (20-31)
- 912 seeded demo members across 3 campuses

## Key Features
- Multi-campus org model with campus switcher dropdown
- Admin ↔ Member toggle (Lyft dual-mode) for users with admin permissions
- Claims-based RBAC (40+ permissions)
- Landing page at `/`, Support page at `/support`
- Apple App Site Association for Universal Links
- War Room, Audit Trail, PDF/CSV Reports, Payment Orchestration (MOCKED)
- Ask Solomon AI Chat (Claude via Emergent LLM Key)
- Sunday Morning Engine, QR Kids Check-in, Volunteer Teams

## Phase A: Planning Center Competitor (IN PROGRESS)
Backend routes done. Frontend pages NOT YET built:
- Services/Worship Planning
- Volunteer Scheduling
- Households
- Member Directory
- Pricing Page
- Church Branding Settings
- Smart Ask Solomon context injection

## Remaining Backlog
- P0: Phase A frontend implementation
- P2: Real Stripe/Pushpay integration
- P2: Push notifications with real VAPID keys
- P2: server.py modular refactor (~15k lines)
- P3: React Native mobile app (90% of usage per user)
