# SOLOMON AI — FULL PLATFORM AUDIT
**Date:** April 2, 2026 | **Auditor:** E1 (Emergent Agent) | **Codebase Version:** Current production

---

## 1. FEATURE INVENTORY — What's Live Today

### A. People Management
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| Member Directory | LIVE | `GET /people`, `GET /people/{id}`, `POST /people`, `PUT /people/{id}`, `DELETE /people/{id}` | `people` (~130,686 docs) | `PeopleList.jsx`, `PersonDetail.jsx` | C/R/U/D |
| Households | LIVE | `GET /households`, `GET /households/{id}`, `POST /admin/households`, `PUT /admin/households/{id}` | `households` (~55,693 docs) | `HouseholdsPage.jsx` | C/R/U/- |
| Contact Info | LIVE | Fields on Person model: email, mobile_phone, work_phone, address (via household) | `people`, `households` | `PersonDetail.jsx` | C/R/U/D |
| Custom Fields | LIVE | `GET/POST/PUT/DELETE /admin/custom-field-definitions`, `GET/PUT /admin/people/{id}/custom-fields`, `PUT /admin/custom-field-definitions/reorder` | `custom_field_definitions` (~3 docs), embedded in `people.custom_fields` | `PersonDetail.jsx`, `SettingsPage.jsx` | C/R/U/D |
| Notes | LIVE | `GET /admin/notes`, `POST /portal/notes` | `leadership_notes` (~4 docs) | `LeadershipNotesPage.jsx` | C/R/-/- |
| Tags/Labels | LIVE | Via `tags` array on Group model; membership_status on Person | `people.membership_status`, `groups.tags` | `PeopleList.jsx` filters | R/U |
| Duplicate Detection | LIVE | `GET /admin/people/duplicates`, `POST /admin/people/merge` | `people` | `DuplicatesPage.jsx` | R/U |
| Smart Lists/Segments | LIVE | `GET /admin/smart-lists`, `POST /admin/smart-lists`, `POST /admin/smart-lists/{id}/run` | `smart_lists` (~6 docs) | `SmartListsPage.jsx` | C/R/-/- |
| CSV Import | LIVE | `POST /admin/members/import/parse`, `POST /admin/members/import/execute` | `people`, `users` | `CSVMemberImport.jsx` | C |
| Leads | LIVE | `GET /admin/leads`, `POST /leads/capture` | `leads` (~17 docs) | `Dashboard.jsx` | C/R |
| Engagement Score | LIVE | Computed field on Person: `engagement_score`, `ytd_giving`, `lifetime_giving`, `last_attended_at` | `people` | `PersonDetail.jsx` | R |

### B. Groups
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| Group Management | LIVE | `GET/POST /admin/groups`, `GET/PUT/DELETE /admin/groups/{id}` | `groups` (~12,477 docs) | `GroupsManagerPage.jsx`, `GroupsList.jsx` | C/R/U/D |
| Group Types | LIVE | `GET /group-types` | `group_types` (~2,448 docs) | `GroupsManagerPage.jsx` | C/R |
| Membership | LIVE | `GET/POST/DELETE /admin/groups/{id}/members` | `group_members` (~259,644 docs) | `GroupDetail.jsx` | C/R/-/D |
| Leaders | LIVE | `leader_id` on Group model, role on GroupMember | `groups.leader_id`, `group_members.role` | `GroupDetail.jsx`, `GroupLeaderDashboard.jsx` | R/U |
| Group Events | LIVE | `GET/POST/PUT/DELETE /admin/groups/{id}/events`, RSVP support | `group_events` (~1 doc) | `GroupDetail.jsx` | C/R/U/D |
| Group Messaging | LIVE | `GET/POST /{group_id}/messages`, `POST /admin/groups/{id}/messages` | `group_messages` (~10 docs) | `GroupDetail.jsx` (via `GroupChat.jsx`) | C/R/-/D |
| Group Q&A | LIVE | `GET/POST /admin/groups/{id}/questions`, `PUT /admin/groups/{id}/questions/{qid}/answer` | `group_questions` (~2 docs) | `GroupDetail.jsx` | C/R/U/- |
| Group Resources | LIVE | `GET/POST/DELETE /admin/groups/{id}/resources` | `group_resources` (~4 docs) | `GroupDetail.jsx` | C/R/-/D |
| Group Attendance | LIVE | `GET /admin/groups/{id}/attendance`, `POST /admin/groups/{id}/attendance` | `group_attendance` (~2 docs) | `GroupDetail.jsx` | C/R |
| Group Outreach | LIVE | `POST /admin/groups/{id}/outreach` | `group_outreach_logs` (~2 docs) | `GroupDetail.jsx` | C/R |
| At-Risk Members | LIVE | `GET /admin/groups/{id}/at-risk` | Computed from `group_members` + `attendance` | `GroupDetail.jsx` | R |
| Join Requests | LIVE | `GET/PUT /admin/groups/{id}/join-requests`, `GET /admin/groups/join-requests/all` | `group_members` (where `status=pending`) | `GroupsManagerPage.jsx`, `GroupDetail.jsx` | C/R/U |
| Portal Group Join/Leave | LIVE | `POST /portal/groups/{id}/join`, `DELETE /portal/groups/{id}/leave` | `group_members` | `PortalGroups.jsx` | C/-/-/D |

### C. Giving & Donations
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| One-Time Giving (Card) | LIVE (via Stripe) | `POST /payments/donate`, `POST /portal/giving/donate`, `POST /solomonpay/process` | `donations` (~871,909 docs), `payment_transactions` (~17 docs) | `PortalGive.jsx`, `SolomonPayAdmin.jsx` | C/R |
| Recurring Giving | LIVE | `GET/POST /portal/recurring-giving`, `PUT /portal/recurring-giving/{id}`, `PUT /portal/recurring-giving/{id}/pause`, `PUT /portal/recurring-giving/{id}/resume`, `DELETE /portal/recurring-giving/{id}` | `recurring_giving` (~18,250 docs) | `PortalGive.jsx`, `GivingDashboard.jsx` | C/R/U/D |
| Fund Management | LIVE | `GET /funds`, `GET/POST/PUT/DELETE /admin/solomonpay/funds/{id}` | `funds` (~3,079 docs) | `SolomonPayAdmin.jsx` (Funds tab) | C/R/U/D |
| Donor Records | LIVE | `GET /admin/solomonpay/donors`, `GET /admin/solomonpay/donors/{id}`, `GET /admin/solomonpay/donor-insights` | `donations`, `people`, `platform_donors` (~15,234 docs) | `SolomonPayAdmin.jsx` (Donors tab) | R |
| Tax Statements (PDF) | LIVE | `GET /admin/giving/year-end-statement/{person_id}`, `GET /portal/giving/statement/{year}`, `GET /portal/giving/statement/{year}/pdf`, `POST /admin/solomonpay/statements/bulk` | `donations`, `statement_jobs` (~3 docs) | `SolomonPayAdmin.jsx` (Statements tab), `PortalGive.jsx` | R |
| Giving History | LIVE | `GET /portal/giving/history`, `GET /portal/giving/ytd`, `GET /people/{id}/giving` | `donations` | `PortalGive.jsx`, `PersonDetail.jsx` | R |
| Batch Entry | LIVE | `GET /batches`, `POST /batches`, `PUT /batches/{id}/close`, `POST /donations` | `donation_batches` (~1,824 docs), `donations` | `GivingDashboard.jsx` | C/R/U |
| Refunds | LIVE | `POST /admin/solomonpay/refund/{donation_id}` | `donations` (status field), `solomonpay_transactions` | `SolomonPayAdmin.jsx` | C |
| Virtual Terminal | LIVE | `POST /admin/solomonpay/virtual-terminal` | `donations`, `solomonpay_transactions` | `SolomonPayAdmin.jsx` (Virtual Terminal tab) | C |
| Pledges | LIVE | `pledges` collection with full model | `pledges` (~6,080 docs) | `GivingDashboard.jsx` | C/R |
| Giving Goals | LIVE | `GET/POST/DELETE /portal/giving-goal` | `giving_goals` (~1 doc) | `PortalGive.jsx` | C/R/-/D |
| Payment Methods | LIVE | `GET/POST/DELETE /payments/methods`, `PUT /payments/methods/{id}/default` | `payment_methods` (~15 docs) | `PortalGive.jsx` | C/R/-/D |
| Cover-the-Fee | LIVE | `cover_fees` field on `GivingDonateRequest` | `donations` | `PortalGive.jsx` | C |
| QR Code Giving | LIVE | `GET /admin/qr/generate` | N/A (generated on-demand) | `SolomonPayAdmin.jsx` (QR tab) | R |
| DonorIQ | LIVE | `GET /admin/solomonpay/donor-insights` | Computed from `donations`, `people` | `SolomonPayAdmin.jsx` (DonorIQ tab) | R |
| Giving Nudge | LIVE | `GET /portal/giving/nudge`, checkout with giving nudge | `donations` | `PortalCafe.jsx`, `PortalMerch.jsx` | R |
| Text-to-Give Config | LIVE | `GET/PUT /admin/sms/text-to-give/config` | `tenants` | `SolomonPayAdmin.jsx` | R/U |

### D. Check-Ins
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| Kids Check-In | LIVE | `POST /admin/kids/{child_id}/checkin`, `POST /admin/kids/checkins/{id}/checkout`, `POST /admin/kids/checkout-by-code`, `POST /admin/kids/verify-pickup` | `checkins` (~30 docs), `children` (~38 docs) | `KidsCheckinAdmin.jsx`, `KidsCheckinModals.jsx`, `CheckedInTab.jsx` | C/R/U |
| Family Registration | LIVE | `POST /admin/kids/register-family` | `children`, `users`, `people` | `RegisterFamilyModal.jsx`, `ManualCheckinModal.jsx` | C |
| Check-In Locations | LIVE | `GET/POST/PUT/DELETE /admin/checkin/locations` | `checkin_locations` (~40 docs) | `CheckInSetupPage.jsx` | C/R/U/D |
| Check-In Stations | LIVE | `GET/POST/PUT/DELETE /admin/checkin/stations` | `checkin_stations` (~16 docs) | `CheckInSetupPage.jsx` | C/R/U/D |
| Labels/Printing | SCAFFOLDED | `GET/POST/PUT/DELETE /admin/checkin/labels`, `POST /admin/printers/print`, `POST /admin/printers/preview` | `checkin_labels` (~11 docs), printer config | `CheckInSetupPage.jsx`, `PrinterConfig.jsx` | C/R/U/D (preview mode only) |
| Medical Alerts | LIVE | `GET /admin/checkin/medical-alerts`, `PUT /admin/checkin/children/{id}/medical` | `children` | `KidsCheckinAdmin.jsx` | R/U |
| Guardians | LIVE | `GET/POST/DELETE /admin/checkin/children/{id}/guardians/{gid}` | `children.guardians` | `KidsCheckinAdmin.jsx` | C/R/-/D |
| Portal Kids Check-In | LIVE | `POST /portal/kids/checkin`, `POST /portal/kids/checkout`, `GET /portal/kids/children` | `checkins`, `children` | `PortalKidsCheckin.jsx` | C/R |
| Adult Service Check-In | LIVE | `POST /portal/attendance/checkin`, `POST /portal/service-checkin`, `POST /portal/attendance/geofence-checkin` | `member_checkins` (~103 docs), `attendance_checkins` (~73 docs) | `PortalHome.jsx` | C/R |
| Check-In Reports | LIVE | `GET /admin/checkin/reports/first-timers`, `GET /admin/checkin/reports/trends`, `GET /admin/kids/checkins/history` | `checkins`, `member_checkins` | `KidsCheckinAdmin.jsx`, `ReportsPage.jsx` | R |
| Geofence Check-In | LIVE | `GET/PUT /admin/geofence/config`, `POST /portal/attendance/geofence-checkin` | `geofence_config` (~4 docs) | `CheckInSetupPage.jsx` | C/R/U |

### E. Services / Worship Planning
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| Service Types | LIVE | `GET /service-types`, `POST /admin/service-types` | `service_types` (~1,836 docs), `service_types_config` (~4 docs) | `ServicesPage.jsx` | C/R |
| Service Plans | LIVE | `GET/POST /admin/services/plans`, `PUT /admin/services/plans/{id}`, `POST /admin/services/plans/{id}/duplicate`, `POST /admin/services/plans/from-template` | `service_plans` (~18 docs) | `ServicesPage.jsx` | C/R/U |
| Plan Templates | LIVE | `GET /admin/services/templates`, `POST /admin/services/templates` | `plan_templates` (~2 docs), `service_templates` (~10 docs) | `ServicesPage.jsx` | C/R |
| Song Library | LIVE | `GET/POST/PUT/DELETE /admin/songs` | `songs` (~12 docs) | `SongLibraryPage.jsx` | C/R/U/D |
| Music Stand View | LIVE | `GET /music-stand/{plan_id}` | `service_plans`, `songs` | `MusicStandPage.jsx` | R |
| Attendance Tracking | LIVE | `POST /attendance`, `GET /attendance/service/{id}` | `attendance` (~1,335,806 docs) | `ServicesPage.jsx` | C/R |

**Missing from Services:** Team position scheduling within plans, rehearsal scheduling, multi-service assignment, arrangement attachments (chord charts, sheet music), live service order management. This is the weakest module vs. Planning Center Services.

### F. Calendar & Events
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| Events | LIVE | `GET/POST/PUT/DELETE /admin/events`, `GET /events`, `GET /events/{id}` | `events` (~3,758 docs) | `EventsManagerPage.jsx`, `EventsPage.jsx` | C/R/U/D |
| Event Registration | LIVE | `POST /register/{event_id}`, `GET /admin/events/{id}/registrations`, `POST /admin/events/{id}/registrations`, `DELETE /admin/events/{id}/registrations/{rid}` | `event_registrations` (~12 docs) | `EventsManagerPage.jsx`, `PublicRegistrationPage.jsx`, `PortalEvents.jsx` | C/R/-/D |
| Room/Resource Booking | LIVE | `GET /admin/calendar/rooms`, `POST /admin/calendar/booking-requests`, `GET /admin/calendar/conflicts`, `GET /admin/calendar/approvals`, `POST /admin/calendar/approvals/{id}`, `POST /admin/calendar/approvals/bulk` | `rooms` (~10 docs), `booking_requests` (~8 docs) | `CalendarApprovals.jsx` | C/R/U |
| Portal Events | LIVE | `GET /portal/events`, `GET /portal/events/registered`, `POST /portal/events/{id}/register`, `DELETE /portal/events/{id}/register` | `events`, `event_registrations` | `PortalEvents.jsx` | C/R/-/D |
| Registration Config | LIVE | `GET/POST /admin/registrations/configs/{event_id}`, `POST /admin/registrations/{event_id}/promo-codes` | `registration_configs` (~2 docs) | `RegistrationsPage.jsx` | C/R |

**Missing from Calendar:** Standalone church calendar view (currently events only, no full calendar component), recurring events, iCal export/subscribe, Google Calendar sync.

### G. Communications
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| Email (via Resend) | LIVE | `POST /admin/communications/send`, `GET /admin/communications/list`, `GET /communications` | `communications` (~2,445 docs) | `CommunicationsPage.jsx` | C/R |
| SMS (Twilio/Scaffold) | SCAFFOLDED | `POST /sms/send`, `POST /sms/bulk`, `POST /admin/sms/send`, `POST /admin/sms/bulk`, `GET /admin/sms/logs`, `POST /sms/incoming`, `GET /sms/templates` | DB-logged (no real delivery without Twilio keys) | `CommunicationsPage.jsx` | C/R |
| Push Notifications | LIVE | `POST /admin/notifications/send`, `GET /vapid-public-key`, `POST /subscribe`, `DELETE /subscribe` | `push_subscriptions` (~1 doc), `notifications` (~376 docs) | `PortalHome.jsx` (subscription) | C/R |
| Announcements | LIVE | `GET/POST/PUT/DELETE /admin/announcements`, `GET /portal/announcements` | `announcements` (~29 docs) | Portal + Admin | C/R/U/D |
| Sunday Morning Broadcast | LIVE | `POST /admin/sunday-morning/broadcast`, `GET /admin/sunday-morning/notification-templates` | `communications` | `Dashboard.jsx` | C |

**Missing from Communications:** Template builder (rich drag-and-drop), scheduled sends, automated drip campaigns, list/segment-based targeting beyond smart lists, email analytics (open rates, click rates), SMS conversation threads.

### H. Registrations & Forms
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| Custom Forms | LIVE | `GET/POST/PUT/DELETE /admin/forms`, `GET /forms/{id}/public`, `POST /forms/{id}/submit`, `GET /admin/forms/{id}/submissions` | `custom_forms` (~12 docs), `form_submissions` (~2 docs) | `FormsPage.jsx`, `PublicRegistrationPage.jsx` | C/R/U/D |
| Event Registration | LIVE | See Calendar section | `event_registrations`, `registration_configs` | `RegistrationsPage.jsx` | C/R/U/D |
| Promo Codes | LIVE | `POST /admin/registrations/{event_id}/promo-codes` | `registration_configs` | `RegistrationsPage.jsx` | C |

**Missing from Registrations:** Payment collection tied to registration (paid events), multi-step forms, conditional logic in forms, form analytics.

### I. Admin & Settings
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| RBAC (12 Roles) | LIVE | `GET /admin/roles/templates`, `GET /admin/roles/users`, `PUT /admin/members/{id}/role`, `PUT /admin/members/{id}/permissions`, `POST /admin/members/{id}/permissions/grant` | `users` | `SettingsPage.jsx` | R/U |
| Multi-Campus | LIVE | `POST /auth/switch-campus`, campus field on Person | `tenants`, `people.campus` | `AppShell.jsx` sidebar | R/U |
| Org Settings / Branding | LIVE | `GET/PUT /admin/settings/branding` | `tenant_branding` (~1 doc) | `SettingsPage.jsx` | R/U |
| API Keys (Developer) | LIVE | `GET/POST/DELETE/PATCH /admin/api-keys` | `agent_api_keys` (~5 docs) | `DeveloperAPIPage.jsx` | C/R/U/D |
| Integrations Page | LIVE | `GET /admin/giving/integrations`, `POST /admin/giving/integrations/connect`, `POST /admin/giving/integrations/disconnect` | `giving_integrations` (~1 doc) | `IntegrationsPage.jsx` | C/R/-/D |
| Audit Log | LIVE | `GET /admin/audit-log` | `audit_log` (~61 docs) | `AuditLogPage.jsx` | R |
| Church Onboarding Wizard | LIVE | `POST /auth/register-church` | `tenants`, `users`, `people` | `SignUpPage.jsx` (onboarding flow) | C |
| Multi-Tenancy | LIVE | tenant_id on every collection, per-request tenant resolution | All collections | Transparent | N/A |

### J. Reporting & Analytics
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| Executive Dashboard | LIVE | `GET /dashboard/stats`, `GET /dashboard/activity`, `GET /dashboard/giving-trend`, `GET /dashboard/attendance-trend`, `GET /dashboard/upcoming-events` | Aggregated from multiple collections | `Dashboard.jsx` | R |
| Giving Reports | LIVE | `GET /admin/giving/report`, `GET /admin/giving/summary`, `GET /admin/reports/giving/summary`, `GET /reports/giving-by-fund`, `GET /reports/giving-by-method`, `GET /reports/top-donors`, `GET /admin/giving/export` | `donations`, `funds` | `ReportsPage.jsx`, `GivingDashboard.jsx` | R |
| Attendance Reports | LIVE | `GET /admin/reports/attendance/summary`, `GET /reports/attendance` | `attendance`, `member_checkins` | `ReportsPage.jsx`, `AttendancePage.jsx` | R |
| Group Reports | LIVE | `GET /reports/groups` | `groups`, `group_members` | `ReportsPage.jsx` | R |
| Kids History Report | LIVE | `GET /reports/kids-history`, `GET /admin/reports/kids/history` | `checkins` | `ReportsPage.jsx` | R |
| Membership Report | LIVE | `GET /reports/membership` | `people` | `ReportsPage.jsx` | R |
| Next Steps Report | LIVE | `GET /reports/next-steps` | `next_steps_journeys` | `ReportsPage.jsx` | R |
| Cafe Report | LIVE | `GET /reports/cafe` | `cafe_orders` | `ReportsPage.jsx` | R |
| Merch Report | LIVE | `GET /reports/merch` | `merch_orders` | `ReportsPage.jsx` | R |
| Report Export (CSV) | LIVE | `GET /reports/{type}/export`, `POST /admin/reports/export` | N/A | `ReportsPage.jsx` | R |
| God Mode Platform Dashboard | LIVE | `GET /api/platform/stats,transactions,payouts,revenue,donors/stats` | Cross-tenant aggregation | `GodModeDashboard.jsx` (7 tabs) | R |

**Missing from Reporting:** Custom report builder, scheduled report delivery, trend comparison (year-over-year), data export in multiple formats (Excel, PDF), embedded BI.

### K. Workflows & Automations
| Feature | Status | API Endpoints | DB Collections | UI Surface | CRUD |
|---------|--------|---------------|----------------|------------|------|
| Workflow Builder | LIVE | `GET/POST/PUT/DELETE /admin/workflows`, `POST /admin/workflows/{id}/enroll`, `GET /admin/workflows/{id}/enrollments` | `workflows` (~4 docs), `workflow_enrollments` (~1 doc) | `WorkflowsPage.jsx` | C/R/U/D |

**Missing from Workflows:** Automatic triggers (new member, first-time visitor, missed attendance), conditional branching, time-delay steps, email/SMS actions within workflow steps, visual workflow builder. Current implementation is a basic manual enrollment system.

### L. Additional Modules (Not in Planning Center)

| Feature | Status | API Endpoints | DB Collections | UI Surface |
|---------|--------|---------------|----------------|------------|
| Ask Solomon AI (Agentic) | LIVE | `POST /solomon/chat`, `POST /solomon/execute-action`, `GET /solomon/history/{session_id}` | `solomon_conversations` (~144 docs) | Chat widget in AppShell |
| 7 AI Action Types | LIVE | cafe_order, merch_order, donation, recurring_giving, event_registration, group_join, checkin | `donations`, `cafe_orders`, `merch_orders`, etc. | Confirmation cards in chat |
| Abundant Cafe | LIVE | Full CRUD for items, orders, settings | `cafe_items` (~63), `cafe_orders` (~758), `cafe_settings` (~7) | `CafeAdminPage.jsx`, `PortalCafe.jsx` |
| Church Merch Store | LIVE | Full CRUD for products, orders | `merch_products` (~55), `merch_orders` (~299) | `MerchAdminPage.jsx`, `PortalMerch.jsx` |
| Media/Sermon Library | LIVE | Videos, sermons, categories, series, watch progress | `media_videos` (~21), `media` (~18), `watch_progress` (~3) | `MediaManagerPage.jsx`, `PortalWatch.jsx`, `PortalLibrary.jsx` |
| Video Notes | LIVE | Take timestamped notes while watching sermons, share | `video_notes` (~3 docs) | `PortalWatch.jsx` |
| Abundant Pathways (LMS) | LIVE | Courses, lessons, modules, enrollment, progress | `pathways_courses` (~8), `pathways_lessons` (~4), `pathways_enrollments` (~14) | `AbundantPathwaysAdmin.jsx`, `PortalPathways.jsx` |
| Solomon Academy (LMS v2) | LIVE | Separate course system with quizzes | `courses` (~12), `course_lessons` (~35), `course_modules` (~11) | `AdminCourseEditor.jsx`, `PortalCourses.jsx` |
| Prayer Wall | LIVE | Create, pray-for, categories, community wall | `prayer_requests` (~10), `prayer_logs` (~5) | `PortalPrayer.jsx` |
| Pastor Meetings | LIVE | Booking slots, recording, transcription | `pastor_meetings` (~4), `pastor_meeting_slots` (~9) | `MeetingsAdminPage.jsx`, `PortalMeetings.jsx` |
| Volunteer Management | LIVE | Opportunities, signups, scheduling, hours log, leaderboard | `volunteer_opportunities` (~12), `volunteer_signups` (~126) | `VolunteerPage.jsx` |
| Attendance Streaks | LIVE | Gamified streaks with badges | `attendance_streaks` (~3 docs) | `PortalHome.jsx` |
| Next Steps / Discipleship | LIVE | Journey approvals, membership milestones | `next_steps` (~15), `next_steps_journeys` (~2) | Various |
| Giving Nudge at Checkout | LIVE | Prompts giving during cafe/merch checkout | `donations` | `PortalCafe.jsx`, `PortalMerch.jsx` |
| War Room (Admin Command) | LIVE | `GET /admin/war-room` | Aggregated | `WarRoom.jsx` |
| Public Developer API | LIVE | `GET /v1/agent/*` (members, events, groups, meetings, visitors, giving, notes, webhooks) | Read-only API with API keys | `DeveloperAPIPage.jsx` |
| WebSocket Real-Time | LIVE | WebSocket connection manager | In-memory | `websocket_service.py` |
| Thinkific Integration | LIVE | `GET/PATCH /admin/thinkific` | `tenants.thinkific_url` | `ThinkificPage.jsx`, `PortalThinkific.jsx` |

---

## 2. PLANNING CENTER PARITY MATRIX

| PC Product | Solomon AI Coverage | What's Missing |
|------------|:---:|----------------|
| **PC People** | **75%** | Missing: field-level permissions, advanced merge rules, inactive-member auto-archival, household-role assignment (head, spouse, child), bulk update tool, people flows (automated journey), directory privacy controls per-member, name pronunciation guide, background check integration, social media profiles |
| **PC Giving** | **85%** | Missing: ACH bank transfers (real), Apple Pay / Google Pay, Stripe Connect multi-entity payout, automated recurring retry on failure, giving analytics comparison (YoY), pledge fulfillment tracking dashboard. **Stripe integration is scaffolded** — donations stay "pending" without real Stripe keys. Solomon Pay vision is a card-present simulation. |
| **PC Groups** | **80%** | Missing: group finder map view, group curriculum/study resources library, group lifecycle automation (auto-archive inactive), group communication templates, group report cards, group-to-group messaging |
| **PC Check-Ins** | **70%** | Missing: real hardware label printing (scaffolded/preview mode only), self-check-in kiosk mode, barcode/QR scanning at station, attendance alerts to parents via SMS on checkout, multiple simultaneous check-in stations with real-time sync, visitor name tag printing, headcount-only check-in |
| **PC Services** | **35%** | Missing: team member position scheduling within plans, rehearsal management, arrangement/chord chart attachments, live service order display, volunteer scheduling integration within service plans, multi-service scheduling view, CCLI reporting, key/tempo metadata on songs, service run-time tracker. **This is the weakest module.** |
| **PC Calendar** | **40%** | Missing: Standalone calendar view component (currently events-only list), recurring events, resource/room conflict resolution UI, calendar sharing/embedding, public calendar feed, iCal/Google Calendar sync, approval workflow is basic |
| **PC Registrations** | **50%** | Missing: Paid event registration with payment collection, multi-step registration forms, conditional logic in forms, waitlist management, group registration, registration capacity enforcement (partial), attendee communications, check-in integration for registered events |

---

## 3. GIVING & PAYMENT INFRASTRUCTURE — Deep Dive

### Payment Processor Integration
- **Stripe**: Integrated via `emergentintegrations.payments.stripe.checkout` library. Uses Stripe Checkout Sessions (redirect flow). Stripe API key and publishable key in `.env`.
- **Solomon Pay**: A proprietary payment brand. Currently a **simulation layer** — the UI accepts card details (card number field is branded as Solomon Pay) but actual charge processing uses Stripe under the hood. The Virtual Terminal collects card info but records donations as "pending" without real charging.

### One-Time Giving
- **Functional**: Yes, via Stripe Checkout redirect and Solomon Pay form.
- **Payment Methods**: Card only. **No ACH, No Apple Pay, No Google Pay**.
- **Cover-the-fee option**: Implemented — donor can opt to cover 1.9% + $0.30.

### Recurring Giving
- **Functional**: Yes. Donors can create, update, pause, resume, and cancel recurring schedules.
- **Frequencies**: Weekly, biweekly, monthly, annually.
- **Self-manage**: Full self-service (pause, cancel, update amount/fund/frequency).
- **Actual charging**: Schedules are stored in DB but **no automated payment execution** — recurring donations are recorded when created but there's no cron/scheduler to actually charge cards on the next_gift_date. This would require Stripe Subscriptions or a background worker.

### Fund/Designation Management
- Full CRUD. Admins can create multiple funds with names, descriptions, goals.
- **Split gifts across funds**: Not natively supported in a single transaction. Donor gives to one fund at a time.

### Donor Statements
- Year-end tax statements: **Functional**. PDF generation via backend. Bulk statement generation job (`POST /admin/solomonpay/statements/bulk`). Portal access for donors (`GET /portal/giving/statement/{year}/pdf`).

### Giving History
- Full donor history: Yes. Filterable by date range, fund. Exportable via CSV (`GET /admin/giving/export`, `GET /admin/solomonpay/transactions/export`).

### Batch Entry
- Manual batch entry for cash/check: **Functional**. `POST /batches` to create a batch, `POST /donations` to add donations to batch, `PUT /batches/{id}/close` to close.

### Refunds/Voids
- `POST /admin/solomonpay/refund/{donation_id}`: Marks donation as refunded in DB. **No actual Stripe refund API call** — would need to be wired up with Stripe Refund API.

### PCI Compliance
- Card data is handled via **Stripe Checkout redirect** (PCI SAQ A — Stripe hosts the payment page). The Solomon Pay Virtual Terminal accepts card details in-browser, which is a PCI concern — card numbers are sent to the backend. In production, this should use Stripe Elements or Stripe Terminal for PCI SAQ A-EP compliance.

### Solomon Pay Vision (Current State)
**Code/infra that exists today:**
- DB schema: `solomonpay_transactions` collection (~10 docs), `payouts` (~510 docs, seeded for demo), `payment_processor_settings` (~2 docs)
- Backend: `routes/solomonpay_admin.py` (574 lines) — full admin dashboard with 8 tabs (Dashboard, Transactions, Donors, DonorIQ, Funds, Statements, Payouts, Virtual Terminal, QR Codes, Settings)
- Fee logic: Card 1.9% + $0.30, ACH 0.8% + $0.30 (hardcoded constants in `platform.py`)
- Payout simulation: Payouts are seeded records showing bank transfers to churches
- **No real acquirer/processor connection**. No card tokenization vault. No PCI-DSS Level 1 compliance. Solomon Pay is currently a branding layer over Stripe.

### Fee Structure
- Card: 1.9% + $0.30 per transaction
- ACH: 0.8% + $0.30 per transaction
- "Cover the fee" option: Donor can opt to cover the processing fee (UI checkbox)
- Industry comparison: Card rate shown vs. industry average ~2.9% + $0.30 — positioning as lower-cost

---

## 4. DATABASE SCHEMA DUMP

**Engine:** MongoDB 7.x (via Motor async driver)
**Connection:** `mongodb://localhost:27017` (local) / Kubernetes-managed in production
**Database Name:** `test_database` (from .env — should be `solomonai` in production)
**Driver:** `motor.motor_asyncio.AsyncIOMotorClient`
**Pool:** min=10, max=50, idle=45s, write concern=majority

### Collections & Estimated Row Counts

| Collection | ~Docs | Key Fields | Relations |
|------------|------:|------------|-----------|
| `users` | 946 | user_id, email, name, password_hash, role, tenant_id, permissions[], person_id, campus_id | → tenants, people |
| `people` | 130,686 | id, tenant_id, first_name, last_name, email, mobile_phone, household_id, membership_status, campus, engagement_score, ytd_giving, lifetime_giving, custom_fields{} | → tenants, households |
| `households` | 55,693 | id, tenant_id, name, address_line1, city, state, zip, phone | → tenants |
| `tenants` | 18 | id, name, subdomain, plan, member_limit, primary_color, subscription_status, address, city, state | Root entity |
| `donations` | 871,909 | id, tenant_id, person_id, fund_id, amount, donation_date, payment_method, is_recurring, recurring_id, batch_id, status, source, fee_amount, net_amount | → tenants, people, funds, recurring_giving |
| `recurring_giving` | 18,250 | id, tenant_id, person_id, fund_id, amount, frequency, next_gift_date, payment_method, is_active | → tenants, people, funds |
| `funds` | 3,079 | id, tenant_id, name, description, is_active, goal_amount, current_amount | → tenants |
| `pledges` | 6,080 | id, tenant_id, person_id, fund_id, pledge_amount, start_date, end_date, total_given | → tenants, people, funds |
| `donation_batches` | 1,824 | id, tenant_id, name, date, status, total_amount, donation_count, created_by | → tenants |
| `payouts` | 510 | id, tenant_id, amount, fee_amount, net_amount, status, bank_last_four, transaction_count, period_start/end | → tenants |
| `platform_donors` | 15,234 | id, tenant_id, person_id, name, email, total_given, donation_count, avg_gift, first_gift_date, last_gift_date, giving_frequency, stage | Cross-tenant donor analytics |
| `groups` | 12,477 | id, tenant_id, name, description, location, meeting_day/time, capacity, is_open, leader_id, group_type_id, enrollment_type, campus_id, member_count | → tenants, people |
| `group_members` | 259,644 | id, tenant_id, group_id, person_id, role, joined_at, is_active | → groups, people |
| `group_types` | 2,448 | id, tenant_id, name, color, icon | → tenants |
| `events` | 3,758 | id, tenant_id, name, description, location, start_datetime, end_datetime, capacity, registration_required, group_id | → tenants, groups |
| `event_registrations` | 12 | id, tenant_id, event_id, user_id/person_id, name, email | → events, tenants |
| `attendance` | 1,335,806 | id, tenant_id, service_id, person_id, group_id, check_in_time | → services, people |
| `services` | 95,472 | id, tenant_id, service_type_id, date, time, total_headcount | → service_types |
| `service_types` | 1,836 | id, tenant_id, name, default_time, default_day | → tenants |
| `service_plans` | 18 | id, tenant_id, name, service_type_id, items[], team[] | → service_types |
| `songs` | 12 | id, tenant_id, title, artist, key, tempo, ccli_number | → tenants |
| `checkins` | 30 | id, tenant_id, child_id, child_name, parent_user_id, pickup_code, classroom, status | → children, users |
| `children` | 38 | id, tenant_id, parent_user_id, name, birthdate, allergies, special_needs, guardians[] | → users |
| `communications` | 2,445 | id, tenant_id, subject, body_html, comm_type, status, recipient_count | → tenants |
| `notifications` | 376 | id, tenant_id, user_id, title, body, read, type | → users |
| `smart_lists` | 6 | id, tenant_id, name, criteria{}, member_count | → tenants |
| `workflows` | 4 | id, tenant_id, name, trigger, steps[] | → tenants |
| `workflow_enrollments` | 1 | id, tenant_id, workflow_id, user_id, current_step, status | → workflows, users |
| `cafe_items` | 63 | id, tenant_id, name, category, price, is_active | → tenants |
| `cafe_orders` | 758 | id, tenant_id, user_id, items[], total, pickup_time, status | → tenants, users |
| `merch_products` | 55 | id, tenant_id, name, price, category, inventory, is_active | → tenants |
| `merch_orders` | 299 | id, tenant_id, user_id, items[], total, status | → tenants, users |
| `media_videos` | 21 | id, tenant_id, title, youtube_id, category_id, series_id, is_featured | → tenants, media_categories |
| `courses` | 12 | id, tenant_id, title, description | → tenants |
| `pathways_courses` | 8 | id, tenant_id, title, category, level, is_published | → tenants |
| `solomon_conversations` | 144 | id, tenant_id, user_id, messages[], session_id | → users |
| `prayer_requests` | 10 | id, tenant_id, user_id, title, content, is_public, prayer_count, status | → users |
| `volunteer_opportunities` | 12 | id, tenant_id, title, description, category | → tenants |
| `volunteer_signups` | 126 | id, tenant_id, user_id, opportunity_id, status | → volunteer_opportunities, users |
| `pastor_meetings` | 4 | id, tenant_id, user_id, slot_id, topic, transcript, summary, status | → pastor_meeting_slots, users |
| `audit_log` | 61 | id, tenant_id, user_id, action, entity_type, entity_id, timestamp | → tenants, users |
| `activity_log` | 4,954 | id, tenant_id, type, description, timestamp | → tenants |
| `user_sessions` | 78 | user_id, session_token, expires_at | → users |

**Indexes:** No custom indexes observed beyond MongoDB's default `_id`. For collections like `donations` (871K docs) and `attendance` (1.3M docs), this is a **major performance concern**. Compound indexes on `{tenant_id, donation_date}`, `{tenant_id, person_id}`, etc. should be added.

**Migrations:** None. No migration framework. Schema changes are applied directly.

---

## 5. INFRASTRUCTURE MAP

> **IMPORTANT:** Solomon AI is deployed on the **Emergent Platform**, NOT Google Cloud Platform directly. The infrastructure is Kubernetes-managed.

### Compute
- **Runtime:** Kubernetes pod on Emergent Platform
- **Backend:** FastAPI (Python 3.x) on uvicorn, managed by Supervisor, port 8001
- **Frontend:** React (Create React App) dev server, port 3000
- **Proxy:** Kubernetes ingress routes `/api/*` → port 8001, all other paths → port 3000

### Database
- **MongoDB** (local instance within pod or managed cluster)
- Connection: `mongodb://localhost:27017`
- DB name: `test_database`
- Pool config: min=10, max=50 connections
- Write concern: majority
- **No HA config observed.** Single-node MongoDB.
- **Backups:** UNCERTAIN — needs manual verification with Emergent Platform

### Storage
- Local file uploads: `/app/backend/uploads/` (tenant-scoped subdirectories)
- **No cloud object storage** (S3, GCS) configured. Uploaded files are on local disk — **will be lost on pod restart**.

### Networking
- External URL: `https://platform-god-mode.preview.emergentagent.com` (preview)
- SSL: Handled by Kubernetes ingress (automatic)
- CORS: Configured via `CORS_ORIGINS` in `.env`

### Auth
- **Custom JWT-like session tokens** (UUID-based, stored in `user_sessions` collection)
- bcrypt password hashing (with SHA256 legacy auto-migration)
- Session-based auth (sessionStorage on frontend, `session_token` → user lookup on backend)
- 12 RBAC role templates (member → platform_admin)
- **No OAuth/SSO** currently (no Google, Facebook, Apple login)

### Async Processing
- **WebSocket service** for real-time updates (in-memory connection manager)
- **No task queue** (no Celery, no Bull, no Pub/Sub). All operations are synchronous request/response.
- Recurring giving has no background scheduler to execute payments.

### Monitoring
- Supervisor process monitoring for backend/frontend
- Backend structured logging (Python `logging` module)
- Security headers middleware (X-Content-Type-Options, HSTS, etc.)
- Correlation ID on 500 errors
- **No external monitoring** (no Datadog, no Sentry, no New Relic)

### CI/CD
- **Emergent Platform**: Automatic deployment from commits
- "Save to GitHub" feature available
- **No custom CI/CD pipeline** (no GitHub Actions, no Cloud Build)

### Multi-Tenancy Model
- **Row-level isolation** via `tenant_id` column on every collection
- Every API request resolves tenant from the authenticated user's `tenant_id`
- Platform admins can query cross-tenant (God Mode)
- **No separate databases per tenant**
- **No row-level security at the DB level** — enforcement is purely at the application layer

### Estimated Costs
- UNCERTAIN — depends on Emergent Platform pricing tier. No GCP-specific billing.

---

## 6. INTEGRATION SURFACE

| Service | Type | Status | Notes |
|---------|------|--------|-------|
| **Stripe** | Payment Processor | SCAFFOLDED (test keys) | `emergentintegrations.payments.stripe.checkout`. Checkout sessions work. Real charging requires live keys. Webhook endpoint exists. Refunds not wired to Stripe API. |
| **Anthropic Claude** (claude-sonnet-4-5) | AI/LLM | LIVE | Via Emergent LLM Key + `emergentintegrations.llm.chat`. Powers Ask Solomon conversational AI. |
| **Resend** | Email Provider | LIVE | `resend` Python library. API key in `.env`. Used for password reset, communications, statement delivery. |
| **Twilio** | SMS Provider | SCAFFOLDED | Graceful degradation: if Twilio keys present, sends real SMS. Otherwise logs to `sms_logs` DB collection. No Twilio keys currently configured. |
| **YouTube** | Video Embed | LIVE | YouTube video IDs stored in media_videos. Embedded via iframe in PortalWatch. No API integration — manual URL entry. |
| **Thinkific** | External LMS | LIVE (embed) | Stores external Thinkific URL and embeds in iframe. No API integration. |
| **Web Push (VAPID)** | Push Notifications | LIVE | VAPID keys in `.env`. Service worker registration for browser push. |
| **Google Calendar** | Calendar Sync | NOT STARTED | No integration exists |
| **CCLI/SongSelect** | Music Licensing | NOT STARTED | CCLI number field exists on Song model but no API integration |
| **Planning Center Import** | Data Migration | NOT STARTED | CSV import exists but no Planning Center-specific adapter |
| **Webhooks (Outbound)** | Developer API | LIVE | `POST /v1/agent/webhooks` — agents can register webhook URLs |
| **Webhooks (Inbound)** | Stripe | LIVE | `POST /webhook/stripe` endpoint for payment status updates |
| **Apple Pay / Google Pay** | Payment Methods | NOT STARTED | Not implemented |
| **ACH Bank Transfers** | Payment Method | NOT STARTED | Fee logic exists (0.8% + $0.30) but no real ACH processor integration |

---

## 7. API SURFACE

### Public/External API
- **Yes**: RESTful API under `/v1/agent/*` namespace
- **Endpoints**: `/v1/agent/members`, `/v1/agent/events`, `/v1/agent/groups`, `/v1/agent/meetings`, `/v1/agent/visitors`, `/v1/agent/giving/summary`, `/v1/agent/notes`, `/v1/agent/webhooks`, `/v1/agent/scout`, `/v1/agent/docs`
- **Total Internal Endpoints**: 538 routes across 35 route files

### Authentication
- API Keys for external consumers (SHA256 hashed, prefix-identified, stored in `agent_api_keys`)
- Session tokens for human users (UUID, stored in `user_sessions`)
- No OAuth2 for external API access

### Documentation
- `GET /v1/agent/docs` returns API documentation JSON
- No Swagger/OpenAPI auto-generated docs exposed (FastAPI has it natively but route not confirmed as exposed)

### Rate Limiting
- In-memory sliding window rate limiter (`check_rate_limit_v2` in core)
- Configurable per API key (`rate_limit` field, default 1000/hour)
- **No distributed rate limiting** — resets on server restart

### Versioning
- `/v1/` prefix on agent API — suggests intent for versioning
- Internal APIs are unversioned (`/admin/*`, `/portal/*`, `/platform/*`)

### Webhook Support
- Outbound webhooks: Agents can register webhook URLs for event notifications
- Inbound: Stripe webhook endpoint

---

## 8. TECHNICAL DEBT & CONSTRAINTS

### Known Bugs / Instability
- **None currently known.** All tests passing (Iteration 77 = 100%).

### Performance Bottlenecks
- **`/api/platform/revenue` endpoint**: ~6 seconds response time. Aggregates across 871K+ donations. Needs MongoDB aggregation pipeline optimization + caching.
- **No database indexes**: Collections like `donations` (871K), `attendance` (1.3M), `people` (130K), `group_members` (260K) have no custom indexes. Queries on `tenant_id + date range` are full collection scans.
- **In-memory rate limiting**: Resets on pod restart. Not suitable for multi-replica deployment.
- **No query pagination defaults**: Some endpoints fetch entire collections.
- **dashboard_stats_cache** collection exists (~11 docs) but unclear if consistently used for cache invalidation.

### Security Concerns
- **Solomon Pay Virtual Terminal**: Accepts raw card numbers in browser → sends to backend. PCI compliance risk. Should use Stripe Elements.
- **No OAuth/SSO**: All auth is email/password. No MFA. No account lockout after failed attempts (rate limiting exists but basic).
- **Session tokens are UUID-based**: Not cryptographically signed JWTs. Session validation requires DB lookup on every request.
- **CORS**: Configured via `.env` — production config needs verification.
- **No CSRF protection**: Session stored in `sessionStorage` (not cookies), which mitigates CSRF but prevents cross-tab session sharing.
- **File uploads**: Stored on local disk without virus scanning or size limits verification.

### Scalability Ceilings
- **~50 concurrent users**: MongoDB connection pool max=50. Beyond this, connection queuing begins.
- **~100-200 concurrent users**: Single-process FastAPI with no horizontal scaling configured. In-memory WebSocket manager and rate limiter are single-instance.
- **~1,000+ users**: Would need: Redis for sessions/rate-limiting/caching, MongoDB replica set, multiple API replicas behind load balancer, async task queue for heavy operations.
- **No CDN**: Static frontend assets served from container.

### Missing Test Coverage
- **Automated tests exist** but are integration-level Playwright/curl tests, not unit tests.
- Test files: `crud_test.py`, `portal_test.py`, `test_code_quality_regression.py`, `test_new_features_iter67.py`, `test_phase3_phase4.py`, `test_phase5_gap_closure.py`, `test_platform_revenue.py`, `test_recurring_giving.py`, `test_refactoring_iter76.py`, `test_solomon_agentic_phase6.py`
- **No frontend unit tests** (no Jest/Vitest configured).
- **No load testing** has been performed.

### Hardcoded Values / Shortcuts
- `DB_NAME=test_database` in production `.env` (should be `solomonai`)
- `PLATFORM_ADMIN_EMAILS` list hardcoded in `database.py` (includes `admin@solomon.ai`, `admin@abundant.org`) — but actual admin is `admin@solomonai.us` (resolved via DB role)
- Default tenant ID `DEFAULT_TENANT_ID` in core module — single-tenant assumption for bootstrapping
- Seed data is mixed with production data (seeded 871K donations for demo, which inflates metrics)

### Outdated Dependencies
- UNCERTAIN — would require `pip list --outdated` and `yarn outdated` to verify. No known CVEs flagged.

---

## 9. WHAT ABUNDANT CHURCH CAN USE TODAY

| Workflow | Production-Ready? | Blocking Issues |
|----------|:--:|-----------------|
| Member directory and search | YES | Scale-tested with 130K+ records |
| Household management | YES | 55K+ households working |
| New visitor follow-up workflow | PARTIAL | Leads capture works, but automated follow-up workflow is manual-enrollment only. No auto-triggers. |
| Small group management and sign-ups | YES | 12K+ groups, 260K memberships, portal join/leave, Q&A, messaging |
| Sunday service check-in (adults) | YES | Geofence + manual + QR check-in options. Service-mode detection. |
| Child check-in with security labels | PARTIAL | Check-in/checkout with pickup codes works. **Label printing is preview/scaffold only** — no real printer output. For a 25K-member church, this is a hard blocker. |
| Online giving (one-time) | PARTIAL | **Stripe test keys only**. UI and flow work. Needs live Stripe keys to process real payments. |
| Recurring giving setup and management | PARTIAL | Donors can create/pause/resume/cancel. **No background scheduler to auto-charge** on recurring dates. Schedules exist but don't execute. |
| Donor tax statements | YES | PDF generation, bulk generation, portal self-service access. Functional with seeded data. |
| Worship service planning and team scheduling | NO | Basic plan creation exists but **no team scheduling within plans, no position assignments, no rehearsal management**. Not viable for a megachurch worship team. |
| Event calendar and registration | PARTIAL | Events + registration works. **No full calendar view**, no recurring events, no paid registration. |
| Email/SMS communications to segments | PARTIAL | Email via Resend works. **SMS is scaffolded only** (no Twilio keys). Smart lists provide segmentation. No template builder. |
| Volunteer scheduling | PARTIAL | Opportunities and signups work. **Scheduling is basic** — no shift management, no auto-assignment, no conflict detection at megachurch scale. |
| Reporting dashboards | YES | Executive dashboard, giving reports, attendance trends, 10+ report types with CSV export. God Mode cross-church analytics. |
| Multi-campus support | YES | 3 Abundant campuses configured and tested. Campus-level filtering on people, groups, donations. |

**Summary: 6 of 15 workflows are production-ready. 7 are partial (need real API keys or feature gaps). 2 are not viable (Services planning, Volunteer scheduling at megachurch scale).**

---

## 10. DIFFERENTIATION — What Solomon AI Does That Incumbents Don't

### 1. Ask Solomon — Agentic AI Assistant (MAJOR DIFFERENTIATOR)
- **Claude-powered conversational AI** built into the admin shell
- 7 action types: cafe ordering, merch ordering, donations, recurring giving, event registration, group joins, kids check-in — all executable via natural language
- **Action confirmation UI**: Solomon proposes an action, user confirms with one click
- Session-based conversation history
- **Neither Planning Center, SecureGive, nor Pushpay has anything like this.**

### 2. Integrated Commerce (Cafe + Merch Store)
- Church cafe ordering system with menu management, time-slot pickup, and order tracking
- Church merchandise store with inventory management
- **Giving nudge at checkout** — prompts users to add a donation when purchasing cafe/merch items
- **No incumbent offers integrated commerce.** This drives both revenue and engagement.

### 3. Abundant Pathways + Solomon Academy (Dual LMS)
- Two separate learning management systems for discipleship
- Video-based lessons with progress tracking, quizzes, certificates
- **Planning Center has no LMS.** Pushpay/SecureGive have no LMS.

### 4. God Mode Platform Dashboard
- Cross-church analytics for platform operators
- $41M+ giving, 560K+ transactions, 510 payouts — real-time aggregated view
- Revenue analytics, fee breakdown, DonorIQ donor lifecycle scoring
- **No incumbent offers a multi-tenant platform admin view** — they are single-org SaaS.

### 5. DonorIQ — AI-Powered Donor Lifecycle Analytics
- Automated donor stage classification (First-Time, Active, Recurring, Lapsed)
- Retention metrics, LTV calculation, giving frequency analysis
- **More sophisticated than Pushpay's donor insights.**

### 6. Prayer Wall with Community Engagement
- Public prayer wall, categories, anonymous posting, prayer count tracking
- Admin dashboard for pastoral care
- **Planning Center has no prayer module.**

### 7. Pastor Meeting Scheduler with Recording/Transcription
- Calendar-style booking for pastoral meetings
- Recording upload and transcription storage
- **No incumbent offers this.**

### 8. Developer API with Webhook Support
- External API for AI agents and integrations (`/v1/agent/*`)
- API key management, rate limiting, webhook registration
- **Planning Center has an API but no agent-specific developer portal.**

### 9. Architectural Advantage — Modern Stack
- **React + FastAPI + MongoDB** vs. Planning Center's Rails monolith
- Real-time WebSocket infrastructure
- True multi-tenant from day one (vs. retrofitted multi-tenancy)
- Potential for faster iteration and AI integration

### 10. Cost Positioning
- Solomon Pay fee structure: **1.9% + $0.30** (card) vs. industry average 2.9% + $0.30
- If Solomon Pay becomes a real processor, the ~1% savings on every transaction is a massive value proposition for high-volume churches like Abundant ($13M+/year giving volume = ~$130K/year savings).

---

## APPENDIX: File Counts & Code Size

| Area | Files | Total Lines |
|------|------:|------------:|
| Backend Routes | 35 | 19,148 |
| Backend Core/Models/Services | ~15 | ~8,000 |
| Frontend Pages (Admin) | ~47 | ~20,000 |
| Frontend Pages (Portal) | ~20 | ~9,000 |
| Frontend Pages (Platform/God Mode) | 8 | ~900 |
| Frontend Components | ~40+ | ~6,000 |
| Pydantic Models | 1 | 1,173 |
| **Total API Endpoints** | — | **538** |
| **Total DB Collections** | — | **~90** |
| **Total Documents** | — | **~3.4M** |
