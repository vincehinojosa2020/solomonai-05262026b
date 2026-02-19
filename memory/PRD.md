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

#### Integration Suite - Competitive with Planning Center

**Active Integrations (5):**
1. **Stripe Payments** - Live donation processing
   - One-time gifts ($25, $50, $100, $250, $500, $1,000 + custom)
   - Recurring monthly donations
   - Multiple payment methods (Card, ACH)
   - Secure Stripe Checkout redirect
   - Webhook handling for payment confirmations

2. **Twilio SMS** - Text messaging (mock mode)
   - Individual SMS to members
   - Bulk SMS to groups
   - 4 message templates
   - 160 character limit with counter
   - Delivery tracking (when configured)

3. **Webhooks** - Real-time event notifications
   - Stripe webhook endpoint `/api/webhook/stripe`
   - Custom endpoint support

4. **Zoom** - Online services (placeholder link)
   - "Join Now" button on dashboard
   
5. **Calendly** - Scheduling (placeholder link)
   - "Schedule Visit" button on dashboard

**Coming Soon Integrations (11):**
- PayPal, Crypto Donations, Resend Email, WhatsApp Business
- Zapier, Checkr, MinistrySafe, YouTube Live
- Google Calendar, AI Assistant (GPT), Slack

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
- **Payments:** Stripe via emergentintegrations library
- **SMS:** Twilio (mock mode until configured)
- **Auth:** Emergent Google OAuth
- **Design:** Inter + JetBrains Mono, DoD-grade palette

---

### API Endpoints

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
| Background Checks | ✅ | 🔜 Coming Soon |
| Zapier | ✅ | 🔜 Coming Soon |
| Crypto Donations | ❌ | 🔜 Coming Soon |
| WhatsApp | ❌ | 🔜 Coming Soon |
| AI Features | ❌ | 🔜 Coming Soon |
| Enterprise UI | ❌ | ✅ DoD-grade |
| Google Auth | Limited | ✅ Full |

---

### Prioritized Backlog

#### P0 - Completed
- [x] Stripe payment integration (live)
- [x] Twilio SMS integration (mock mode)
- [x] Integrations showcase page
- [x] Google OAuth authentication
- [x] DoD-grade enterprise UI
- [x] All core modules functional

#### P1 - Next Phase
- [ ] Configure Twilio credentials for live SMS
- [ ] Resend email integration
- [ ] Checkr background checks
- [ ] Zapier webhooks/triggers
- [ ] PDF Giving statements

#### P2 - Future
- [ ] PayPal donations
- [ ] Crypto donations (Bitcoin, Ethereum)
- [ ] WhatsApp Business integration
- [ ] AI Assistant (GPT sermon summaries)
- [ ] Slack notifications
- [ ] YouTube Live embed
- [ ] Google Calendar sync

---

### Test Credentials

- **Session Token:** test_session_1771463210214
- **Test User:** admin@abundantchurch.org / Admin User
- **Stripe Key:** sk_test_emergent (test mode)

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

1. Configure Twilio credentials for live SMS
2. Implement Resend email integration
3. Add Checkr background check integration
4. Create Zapier triggers/actions
5. Implement giving statement PDF generation
6. Add real Zoom/Calendly links from user
