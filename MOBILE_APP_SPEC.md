# Solomon AI — Mobile App Specification
## For Expo React Native Conversion

### Backend API Base URL
```
https://secure-deploy-17.preview.emergentagent.com/api
```

### Authentication
All authenticated endpoints accept Bearer token in the `Authorization` header:
```
Authorization: Bearer <session_token>
```

**Login**: `POST /api/auth/login`
```json
// Request
{ "email": "member@abundant.church", "password": "Demo2026!" }
// Response
{
  "user_id": "...",
  "email": "member@abundant.church",
  "name": "Maria Gonzalez",
  "role": "member",
  "tenant_id": "abundant-church-001",
  "tenant_name": "Abundant Church",
  "session_token": "sess_..." // ← Store this in SecureStore for mobile
}
```

**Register**: `POST /api/auth/register`
```json
// Request
{
  "email": "...",
  "password": "...",
  "first_name": "...",
  "last_name": "...",
  "church_name": "My Church"
}
// Response includes session_token
```

**Get Current User**: `GET /api/auth/me`

---

## MOBILE APP SCREENS & NAVIGATION

### Tab Bar (Bottom Navigation)
1. **Home** → PortalHome
2. **Watch** → Abundant TV video content
3. **Give** → Donations/giving
4. **Groups** → Small groups + chat
5. **More** → Events, Kids Check-in, Café, Merch, Settings

---

## SCREEN-BY-SCREEN API MAPPING

### 1. HOME SCREEN
**API Calls:**
- `GET /api/portal/me` — Member profile + stats
- `GET /api/portal/events` — Upcoming events list
- `GET /api/portal/service-mode` — Active service banner
- `GET /api/portal/attendance-streak` — Attendance streak data

**UI Elements:**
- Welcome greeting with user name
- Service Mode banner (when active)
- Attendance streak card (flame icon, current streak)
- Quick action buttons (Give, Watch, Kids, Events)
- Upcoming events list (date chip, name, location, time)

---

### 2. WATCH SCREEN (Abundant TV)
**API Calls:**
- `GET /api/admin/watch/categories` — Video categories
- `GET /api/admin/watch/videos` — All videos
- `GET /api/portal/watch/progress` — User's watch progress
- `POST /api/portal/watch/progress` — Update watch progress
- `POST /api/portal/video-notes` — Save notes on a video
- `GET /api/portal/video-notes/video/{videoId}` — Get notes for video

**UI Elements:**
- Category filter pills (All, Sermons, Worship, etc.)
- Video cards with thumbnails, duration, progress bar
- Video player with Masterclass-style side notes panel
- Notes editor (per video)

---

### 3. GIVE SCREEN
**API Calls:**
- `GET /api/portal/giving/history` — Donation history
- `POST /api/donations` — Create a donation
- `GET /api/funds` — Available giving funds

**UI Elements:**
- Quick amount buttons ($25, $50, $100, $250)
- Custom amount input
- Fund selector (General, Building, Missions)
- Payment method (Stripe integration)
- Giving history list

---

### 4. GROUPS SCREEN
**API Calls:**
- `GET /api/portal/groups` — All available groups
- `GET /api/portal/my-groups` — Joined groups
- `POST /api/portal/groups/{groupId}/join` — Join a group
- `POST /api/portal/groups/{groupId}/leave` — Leave a group
- `GET /api/groups/{groupId}/messages` — Group chat messages
- `POST /api/groups/{groupId}/messages` — Send chat message
- `DELETE /api/groups/{groupId}/messages/{messageId}` — Delete message

**UI Elements:**
- Filter tabs (All Groups, My Groups)
- Group type filter (Bible Study, Service Team, etc.)
- Group cards (name, type, schedule, member count, location)
- **Group Chat** (full messaging UI):
  - Message bubbles (blue=mine, white=others)
  - Sender name + admin badge
  - Date separators
  - Send input with submit button
  - 5-second polling for new messages

---

### 5. EVENTS SCREEN
**API Calls:**
- `GET /api/portal/events` — All upcoming events (includes waitlist_count)
- `GET /api/portal/my-events` — Registered events
- `POST /api/portal/events/{eventId}/register` — Register for event
- `DELETE /api/portal/events/{eventId}/register` — Cancel registration

**UI Elements:**
- Hero banner (featured event)
- Category pills (Worship, Women, Men, Youth, Community, Conferences)
- Filter tabs (All, This Week, This Month, My Events)
- Event cards:
  - Date chip (month/day)
  - Name, location, time
  - Capacity progress bar (X/Y spots)
  - Ticket tiers (Free, VIP, Premium)
  - Waitlist count
  - Register / Join Waitlist / Registered status
  - Share button
- Event detail modal (full info, capacity bar, tier list)

---

### 6. KIDS CHECK-IN SCREEN
**Design: Duolingo / Veggie Tales aesthetic with Nunito font**

**API Calls:**
- `GET /api/portal/kids` — List children
- `POST /api/portal/kids` — Add a child
- `DELETE /api/portal/kids/{childId}` — Remove a child
- `POST /api/portal/kids/{childId}/checkin` — Check in
- `GET /api/portal/kids/checkins/active` — Active check-ins

**UI Elements:**
- Green header "Kids Zone — Sunday School Adventures"
- Child cards with DiceBear avatars: `https://api.dicebear.com/7.x/adventurer/svg?seed={name}`
- Vibrant color palette: #58CC02, #CE82FF, #FF9600, #1CB0F6, #FF4B4B, #FFC800
- Character badge per child (Explorer, Dreamer, Hero, etc.)
- **3-Step Check-in Wizard** (bottom sheet):
  1. Select children (tap to select, green checkmarks)
  2. Confirm (child list with details)
  3. Success (QR codes + 3-digit pickup codes)
- Add Child modal (name*, birthdate*, allergies, special needs, emergency contact)
- Active summary bar (X children in Sunday School)

---

### 7. CAFÉ SCREEN
**API Calls:**
- `GET /api/portal/cafe/settings` — Café settings
- `GET /api/portal/cafe/items` — Menu items
- `POST /api/portal/cafe/orders` — Place order

**UI Elements:**
- Category tabs for menu items
- Item cards with price, description
- Cart with quantity controls
- Giving nudge component (optional add-on donation)

---

### 8. MERCH SCREEN
**API Calls:**
- `GET /api/portal/merch/products` — Product catalog
- `POST /api/portal/merch/orders` — Place order

**UI Elements:**
- Product grid (image, name, price, category)
- Search bar
- Product detail view
- Cart
- **Merch Recommender chatbot** (floating button, pattern-matching product suggestions)
- Giving nudge component

---

### 9. PUSH NOTIFICATIONS
**API Calls:**
- `GET /api/push/vapid-public-key` — Get VAPID public key
- `POST /api/push/subscribe` — Subscribe to push
- `DELETE /api/push/subscribe` — Unsubscribe

**Triggers (server-side, already implemented):**
- New group message → notify other group members
- Event registration → confirmation push to user
- Kids checkout → notify parent

**For Expo**: Use `expo-notifications` for push, register device token with backend.

---

### 10. SETTINGS / PROFILE
**API Calls:**
- `GET /api/auth/me` — Current user info
- `POST /api/auth/logout` — Logout

---

## COLOR SYSTEM
```
Primary Blue: #3b82f6
Dark Navy: #0f172a / #1e293b
Green (Kids): #58CC02
Orange: #FF9600
Success: #22c55e
Error: #ef4444
Warning: #f59e0b
Background: #f8fafc
Card: #ffffff
Text Primary: #0f172a
Text Secondary: #64748b
Text Muted: #94a3b8
```

## FONTS
- **Primary**: Inter (weights: 400, 500, 600, 700)
- **Kids Zone**: Nunito (weights: 400, 600, 700, 800, 900)

## TEST ACCOUNTS
| Role | Email | Password |
|------|-------|----------|
| Platform Admin | admin@solomon.ai | Demo2026! |
| Church Admin | admin@abundant.church | Demo2026! |
| Member | member@abundant.church | Demo2026! |

## KEY NOTES FOR MOBILE AGENT
1. **Auth**: Store `session_token` from login response in `expo-secure-store`. Send as `Authorization: Bearer <token>` header on every request.
2. **CORS**: Backend allows all origins (`*`) — no CORS issues for mobile.
3. **Push**: Backend has VAPID keys and push subscription endpoints. Use `expo-notifications` for device token management.
4. **DiceBear Avatars**: Kids screen uses external SVG avatars from DiceBear API — render with `react-native-svg` or as WebView.
5. **QR Codes**: Kids check-in generates QR codes — use `react-native-qrcode-svg`.
6. **Real-time**: Group chat polls every 5 seconds. Consider upgrading to WebSockets for mobile.
7. **Stripe**: Giving uses Stripe — integrate with `@stripe/stripe-react-native`.
