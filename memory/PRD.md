# Samson - Enterprise Church Management SaaS Platform
## Product Requirements Document

### Overview
**Product Name:** SAMSON  
**Tagline:** "Enterprise Church Management System"  
**Demo Tenant:** Abundant Church (El Paso, TX)  
**Target Scale:** 50,000+ members per tenant  
**Target Audience:** Mega churches (Lakewood, Potter's House, Elevation Church)  
**Competitive Target:** Planning Center (planningcenter.com)

---

### What Was Implemented (February 2026)

#### 🔵 UPGRADE 1: Solomon AI Analyst (P0 - COMPLETED)
**AI-Powered Church Intelligence Assistant using Claude Sonnet 4.5**

- **Floating "Ask Solomon" button** - Blue gradient FAB in bottom-right corner
- **Slide-up chat panel** - 420px wide, 600px tall with smooth animations
- **Welcome screen** with description and 4 sample prompts:
  - "How are our giving trends this month?"
  - "Which members need follow-up?"
  - "Summarize our group engagement"
  - "What events are coming up?"
- **Real-time church context** - Solomon queries live database for:
  - Membership counts (total, active, visitors)
  - Giving stats (MTD, YTD, goals)
  - Group engagement metrics
  - Recent activity feed
  - Upcoming events
- **Smart action suggestions** - Contextual buttons linking to relevant pages
- **Conversation history** - Stored in MongoDB `solomon_conversations` collection
- **Session management** - Clear chat functionality

**API Endpoints:**
- `POST /api/solomon/chat` - Send message, get AI response
- `GET /api/solomon/history/{session_id}` - Get conversation history
- `DELETE /api/solomon/session/{session_id}` - Clear session

**Integration:** Claude Sonnet 4.5 via Emergent LLM Key (emergentintegrations library)

---

#### Integration Suite - Competitive with Planning Center

**Active Integrations (6):**
1. **Solomon AI** (NEW) - AI church analyst powered by Claude Sonnet 4.5
   - Natural language queries about church data
   - Pastoral advice and strategic recommendations
   - Contextual action suggestions
   
2. **Stripe Payments** - Live donation processing
   - One-time gifts ($25, $50, $100, $250, $500, $1,000 + custom)
   - Recurring monthly donations
   - Multiple payment methods (Card, ACH)
   - Secure Stripe Checkout redirect
   - Webhook handling for payment confirmations

3. **Twilio SMS** - Text messaging (mock mode)
   - Individual SMS to members
   - Bulk SMS to groups
   - 4 message templates
   - 160 character limit with counter
   - Delivery tracking (when configured)

4. **Webhooks** - Real-time event notifications
   - Stripe webhook endpoint `/api/webhook/stripe`
   - Custom endpoint support

5. **Zoom** - Online services (placeholder link)
   - "Join Now" button on dashboard
   
6. **Calendly** - Scheduling (placeholder link)
   - "Schedule Visit" button on dashboard

**Coming Soon Integrations (10):**
- PayPal, Crypto Donations, Resend Email, WhatsApp Business
- Zapier, Checkr, MinistrySafe, YouTube Live
- Google Calendar, Slack

---

#### DoD-Grade Enterprise UI
- Palantir/Bloomberg-inspired design
- Sharp corners, utilitarian layout
- Data-dense with monospace numbers
- Dark slate sidebar (#0f172a)
- Blue accent (#3b82f6)

#### Google OAuth Authentication
- Emergent Auth integration
- Session management with httpOnly cookies
- Protected routes with auth guard
- User profile and logout

#### Core Modules
- Dashboard with real-time stats
- Members (201 seeded)
- Groups (20 seeded)
- Stewardship/Giving with Stripe checkout
- Communications with Email + SMS tabs
- Attendance tracking
- Reports and Settings
- Integrations showcase page

---

### Technical Stack

- **Frontend:** React 18, React Router, Recharts, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI, Motor (async MongoDB)
- **Database:** MongoDB
- **AI:** Claude Sonnet 4.5 via emergentintegrations (Emergent LLM Key)
- **Payments:** Stripe via emergentintegrations library
- **SMS:** Twilio (mock mode until configured)
- **Auth:** Emergent Google OAuth
- **Design:** Inter + JetBrains Mono, DoD-grade palette

---

### API Endpoints

**Solomon AI:**
- `POST /api/solomon/chat` - Chat with Solomon AI analyst
- `GET /api/solomon/history/{session_id}` - Get conversation history
- `DELETE /api/solomon/session/{session_id}` - Clear chat session

**Payments:**
- `POST /api/payments/donate` - Create Stripe checkout session
- `GET /api/payments/status/{session_id}` - Check payment status
- `POST /api/webhook/stripe` - Stripe webhook handler

**SMS:**
- `POST /api/sms/send` - Send individual SMS
- `POST /api/sms/bulk` - Send bulk SMS to group
- `GET /api/sms/templates` - Get SMS templates

**Auth:**
- `POST /api/auth/session` - Exchange session_id for user data
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

---

### Seeded Demo Data

| Entity | Count |
|--------|-------|
| Tenant | 1 (Abundant Church) |
| Households | 80 |
| People | 201 |
| Groups | 20 |
| Funds | 5 |
| Donations | 4,710 |
| Recurring Giving | 30 |
| Events | 6 |

---

### Competitive Analysis vs Planning Center

| Feature | Planning Center | SAMSON |
|---------|-----------------|--------|
| Stripe Payments | ✅ | ✅ |
| SMS Messaging | Via 3rd party | ✅ Built-in |
| AI Assistant | ❌ | ✅ Solomon AI |
| Background Checks | ✅ | 🔜 Coming Soon |
| Zapier | ✅ | 🔜 Coming Soon |
| Crypto Donations | ❌ | 🔜 Coming Soon |
| WhatsApp | ❌ | 🔜 Coming Soon |
| Enterprise UI | ❌ | ✅ DoD-grade |
| Google Auth | Limited | ✅ Full |

---

### Prioritized Backlog

#### P0 - Completed ✅
- [x] Stripe payment integration (live)
- [x] Twilio SMS integration (mock mode)
- [x] Integrations showcase page
- [x] Google OAuth authentication
- [x] DoD-grade enterprise UI
- [x] All core modules functional
- [x] **Solomon AI Analyst** (Claude Sonnet 4.5)

#### P1 - Next Phase (From Master Upgrade Prompt)
- [ ] **UPGRADE 2:** Design System Elevation - Sora/JetBrains Mono fonts, premium stat cards
- [ ] **UPGRADE 6:** Dashboard Intelligence - Fix attendance chart, Solomon Insights widget, "This Sunday" card
- [ ] Configure Twilio credentials for live SMS
- [ ] Resend email integration

#### P2 - Future
- [ ] **UPGRADE 5:** Giving Module Completion - Record Gift panel, crypto support
- [ ] **UPGRADE 3:** Missing Modules - Workflows, Check-In, Services
- [ ] **UPGRADE 10:** Communications Upgrade - AI writer, rich text editor
- [ ] **UPGRADE 8:** Global Search (⌘K command palette)
- [ ] **UPGRADE 4:** Reports Expansion
- [ ] **UPGRADE 7:** Micro-interactions (Framer Motion)
- [ ] PayPal donations
- [ ] Crypto donations (Bitcoin, Ethereum)
- [ ] WhatsApp Business integration
- [ ] Slack notifications
- [ ] YouTube Live embed
- [ ] Google Calendar sync

---

### Test Credentials

- **Session Token:** test_session_1771463210214
- **Test User:** admin@abundantchurch.org / Admin User
- **Stripe Key:** sk_test_emergent (test mode)
- **Emergent LLM Key:** Configured in backend/.env

---

### MOCKED/PLACEHOLDER Items

- **Twilio SMS:** Mock mode (returns mock_* message IDs)
- **Zoom Link:** https://zoom.us/j/placeholder
- **Calendly Link:** https://calendly.com/placeholder
- **PayPal:** paypal.me/placeholder
- **Venmo:** venmo.com/placeholder
- **Resend Email:** Not configured

---

### Next Action Items

1. **P1:** UPGRADE 2 - Design System Elevation (fonts, premium styling)
2. **P1:** UPGRADE 6 - Dashboard Intelligence (charts, widgets)
3. Configure Twilio credentials for live SMS
4. Implement Resend email integration
5. Add Checkr background check integration

---

### Code Architecture

```
/app/
├── backend/
│   ├── server.py       # FastAPI with all routes (incl. Solomon AI)
│   ├── tests/          # pytest test files
│   └── .env            # MONGO_URL, STRIPE_API_KEY, EMERGENT_LLM_KEY
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SolomonChat.jsx    # Solomon AI floating chat
│   │   │   ├── layout/AppShell.jsx
│   │   │   └── modals/
│   │   ├── pages/
│   │   └── App.css                # Includes Solomon styles
│   └── .env
└── memory/
    └── PRD.md
```
