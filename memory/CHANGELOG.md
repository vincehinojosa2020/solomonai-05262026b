# Solomon AI — Changelog

## March 26, 2026 (Fork Session - Quality Improvements)

### 7E: Attendance Streaks Seed
- Seeded 12 consecutive Sunday check-ins for Shannon Nieman and Jacob Pacheco
- Both users now show current_streak=12, longest_streak=12, total_attended=12
- 3 badges earned: "Month Strong", "2 Month Champion", "Quarter Master"

### 7C: Member Directory Seed
- Added 25 realistic member profiles to `people` collection for abundant-east-001 tenant
- Fixed directory endpoint to fallback to `first_name + last_name` when `name` field is empty
- Directory now shows 229 total members with names, groups, and search capability

### 7D: Solomon Chat Context Injection
- Fixed `solomon_chat` endpoint to pass `user` object to `get_church_context()` 
- Chat now includes personalized member context (name, groups) in LLM prompt
- Live church data injected: membership stats, events, announcements, service plans

### Giving Platform Integration Scaffold
- Added 3 backend endpoints: GET integrations, POST connect, POST disconnect
- Created admin UI section in GivingDashboard with Solomon Pay, Pushpay, SecureGive cards
- Processor switching works (connect/disconnect with active state management)
- Seed data sets Solomon Pay as default active processor
- All integrations are MOCKED for demo; real processor connections planned for future

### Bug Fixes
- Fixed Member Directory showing empty names for bulk-seeded members (fallback to first_name + last_name)
- Added auth headers to GivingDashboard integration API calls
