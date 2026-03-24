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
- **Promote to Admin**: Platform admin changes any member's role
- **Multi-Campus**: Campus switcher for org-level admins (Abundant: East, Downtown, West)
- **Admin/Member Toggle**: Users with admin permissions switch between admin and member views
- **Church Isolation**: Church admins cannot see other churches or platform-level data

## Solomon Academy (LMS) — COMPLETED (March 2026)
**Full native LMS replacing Thinkific. Accessible by both admins and members.**

### Admin Side (`/admin/courses`)
- Course list table with status badges, enrollment counts, completion rates
- Course builder with 3 tabs (Info, Curriculum, Settings)
- Module management (create, edit, delete, reorder with arrows)
- 4 lesson types: Video (YouTube/Vimeo embed), Text (Markdown), Quiz (MCQ with scoring), Download (external URL)
- Enrolled members view with progress tracking

### Portal Side (`/portal/courses`)
- Course catalog with tabs (All / My Courses / Completed)
- Course detail with hero, description, curriculum outline
- Enrollment system (click Enroll → access lessons)
- Lesson viewer for all 4 types (video/text/quiz/download)
- Progress tracking (% complete, checkmarks on completed lessons)
- Quiz grading with pass/fail and retry

### Seed Data: "Abundant Next Steps"
- 5 modules, 7 lessons (2 video, 4 text, 1 quiz)
- Mirrors Abundant Church's Thinkific course
- Status: Published, Enrollment: Open

### New MongoDB Collections
- `courses`, `course_modules`, `course_lessons`, `course_enrollments`, `course_lesson_progress`

### New Permissions
- `admin.courses.view`, `admin.courses.edit` (added to church_admin template)
- `member.courses` (added to member permissions)

## Phase A: Planning Center Competitor — COMPLETED (March 2026)
- Pricing Page (`/pricing`): 3 tiers (Starter/Free, Growth/$99, Enterprise/$249)
- Services/Worship Planning (`/services`): Service plans, items, status management
- Volunteer Scheduling (`/volunteers`): Teams + Schedule tabs
- Households (`/households`): Family management with address and search
- Member Directory (`/portal/directory`): Privacy-respecting member search
- Church Branding (`/settings` Appearance tab): App name, tagline, color, logo

## Completed Features (All Sessions)
- Multi-Campus Switcher UI + backend
- "Lyft-style" Admin/Member view toggle
- Public Landing Page (`/`) and Support Page (`/support`)
- Apple AASA file for iOS universal links
- Platform Dashboard: Create User & Promote to Admin
- Startup DB Seed script (safe upserts)
- Production Auth Bug RESOLVED
- Phase A frontend pages (6 pages)
- Solomon Academy (full LMS)

## Backlog
- P2: Real Stripe/Pushpay integration (currently mocked)
- P2: Push notifications with real VAPID keys
- P2: server.py modular refactor (~16k lines)
- P2: PDF certificates for course completion
- P2: File upload for download-type lessons
- P2: Auto-enroll new members in courses
- P3: React Native mobile app

## Architecture
```
/app/
├── backend/
│   ├── server.py                 # ~16K line monolith
│   └── routes/
│       ├── courses.py            # Solomon Academy APIs (separate router)
│       ├── volunteer.py          # Volunteer APIs
│       ├── giving_nudge.py       # Giving nudge APIs
│       └── push.py               # Push notifications
├── frontend/
│   └── src/
│       ├── pages/admin/
│       │   ├── AdminCourseList.jsx
│       │   ├── AdminCourseEditor.jsx
│       │   └── AdminCourseMembers.jsx
│       ├── pages/portal/
│       │   ├── PortalCourses.jsx
│       │   ├── PortalCourseDetail.jsx
│       │   └── PortalLessonViewer.jsx
│       └── components/layout/
│           ├── AppShell.jsx       # Admin sidebar (Courses in MINISTRY)
│           └── PortalLayout.jsx   # Portal nav (Courses link)
```

## 3rd Party Integrations
- Anthropic Claude (Ask Solomon) — uses Emergent LLM Key
- Stripe/Pushpay — MOCKED
- react-markdown — for text lesson rendering
