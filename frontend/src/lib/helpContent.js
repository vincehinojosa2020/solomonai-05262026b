/**
 * Solomon AI — Contextual Help Content Registry
 * Every feature key maps to: what, howTo, proTip, and learnMore links.
 */

export const HELP_CONTENT = {
  // ── Giving / Stewardship ──────────────────────────────────────────
  giving: {
    title: 'Stewardship Dashboard',
    what: 'Track all giving activity, manage recurring gifts, and monitor fund progress for your church.',
    howTo: [
      'Click "Record Gift" to enter a manual cash, check, or card donation.',
      'Use "Export CSV" to download all giving records for accounting.',
      'The Payment Channels section shows available giving methods for your congregation.',
      'Recurring gifts are managed in the Recurring Giving section — pause, resume, or cancel anytime.',
      'Fund Progress bars show YTD giving toward each fund goal.',
    ],
    proTip: 'Set giving goals on each fund to keep the congregation motivated. Goals appear as progress bars on the member portal.',
    support: true,
  },
  donationCheckout: {
    title: 'Online Giving',
    what: 'Securely accept card and ACH donations through Solomon Pay — no third-party accounts required.',
    howTo: [
      'Select a fund designation (General, Building, Missions, etc.).',
      'Choose a preset amount or enter a custom dollar amount.',
      'Optionally make the gift monthly recurring.',
      'Enter card details — Solomon Pay tokenizes the card so raw card data is never stored.',
      'Click "Complete Gift" to process the charge.',
    ],
    proTip: 'Donors who cover the processing fee (1.9% + $0.30) ensure 100% of the intended gift goes to the church.',
    support: true,
  },
  recurringGiving: {
    title: 'Recurring Giving',
    what: 'Automatically processes scheduled gifts on a weekly, bi-weekly, monthly, or annual basis through Solomon Pay.',
    howTo: [
      'Members set up recurring gifts from the member portal under "My Giving".',
      'The scheduler runs every hour, charging all due schedules.',
      'Failed charges retry once per day for up to 3 days.',
      'After 3 consecutive failures, the schedule is auto-paused and the donor is notified.',
      'Use "Run Now" to trigger an immediate batch run for testing.',
    ],
    proTip: 'Encourage members to set up monthly recurring gifts — churches with 30%+ recurring donor rates have much more predictable cash flow.',
    support: true,
  },
  funds: {
    title: 'Giving Funds',
    what: 'Funds are designated pools for charitable contributions (e.g., General, Building, Missions, Youth Ministry).',
    howTo: [
      'Create a new fund with a name, optional goal amount, and start/end dates.',
      'Set a goal amount to enable the progress bar on the member portal.',
      'Archive a fund to stop accepting new gifts without deleting historical data.',
      'Funds appear in giving dropdowns for donors and in the batch entry form.',
    ],
    proTip: 'Capital campaign funds with visible progress bars (e.g., "New Sanctuary — $2.1M / $3M") dramatically increase giving engagement.',
    support: true,
  },

  // ── People ────────────────────────────────────────────────────────
  people: {
    title: 'People Directory',
    what: 'The central database of all members, visitors, and contacts for your church.',
    howTo: [
      'Search by name, email, or phone using the search bar.',
      'Filter by membership status (member, regular, visitor) using the status dropdown.',
      'Click any person to view their full profile, giving history, and group memberships.',
      'Use "Add Person" to manually enter a new contact.',
      'Export the directory to CSV for mail merges or integrations.',
    ],
    proTip: 'Use custom fields (Admin → Settings → Custom Fields) to track anything specific to your church — small group interest, spiritual gifts, volunteer training status, etc.',
    support: true,
  },
  households: {
    title: 'Households',
    what: 'Group family members together under a single household for address management and giving reports.',
    howTo: [
      'Create a household and assign a Head of Household.',
      'Add family members (Spouse, Children, Other) to the household.',
      'Household giving total combines all members\' donations for tax statements.',
      'Use the household address for mailings and directory listings.',
    ],
    proTip: 'Set the household "giving coordinator" to control who receives tax statements — especially important for families that tithe jointly.',
    support: true,
  },

  // ── Groups ────────────────────────────────────────────────────────
  groups: {
    title: 'Small Groups',
    what: 'Manage home groups, Bible studies, ministry teams, and any other gathering of people.',
    howTo: [
      'Create a group with a name, leader, meeting schedule, and max capacity.',
      'Add members directly or allow members to request to join from the portal.',
      'Track attendance for each group meeting.',
      'Send group-specific communications from the group detail page.',
      'Use group tags to organize groups by type (Community Group, Ministry Team, etc.).',
    ],
    proTip: 'Groups with a regular published meeting schedule get 40% more portal sign-ups. Always fill in meeting day and time.',
    support: true,
  },

  // ── Check-In ──────────────────────────────────────────────────────
  checkin: {
    title: 'Kids Check-In',
    what: "Secure, code-based check-in system for children\'s ministry. Every child gets a unique pickup code each service.",
    howTo: [
      'Check in a child by searching their name or scanning a QR code.',
      'A unique 4-character pickup code is generated and printed on the child label.',
      'Parents keep the pickup receipt to claim their children at dismissal.',
      'Use "Launch Kiosk Mode" for a self-service family check-in station.',
      'Verify checkout by matching the parent\'s pickup code before releasing a child.',
    ],
    proTip: 'Place kiosk stations at every entrance with a volunteer nearby for first-timers — this reduces lobby congestion by 60%.',
    support: true,
  },
  kioskMode: {
    title: 'Kiosk Check-In Mode',
    what: 'Full-screen, touch-friendly self-service check-in for families to check in their children without staff assistance.',
    howTo: [
      'Click "Launch Kiosk Mode" from Check-In Setup.',
      'Families enter their phone number to find their registered children.',
      'Select which children to check in and confirm.',
      'Labels print automatically (if a printer is connected) or display pickup codes on screen.',
      'Exit kiosk mode requires a 4-digit admin PIN (default: 1234 — change in Settings).',
    ],
    proTip: 'Set up kiosks on iPad minis or repurposed tablets at $99/each. Mount at 42" height for easy adult access.',
    support: true,
  },

  // ── Services ──────────────────────────────────────────────────────
  services: {
    title: 'Service Plans',
    what: 'Plan every element of your worship service — songs, scripture, message, transitions, and team assignments.',
    howTo: [
      'Create a service plan and set the date and service type.',
      'Add items (Song, Scripture, Prayer, Message, Offering, etc.) in order.',
      'Assign volunteers to positions (Worship Leader, Sound, Slides, etc.).',
      'Export the plan as a PDF to share with your team.',
      'Use "Live Mode" during service to follow along on a tablet.',
    ],
    proTip: 'Link rehearsal events to service plans — team members get auto-invitations and can confirm availability from the portal.',
    support: true,
  },

  // ── Events ────────────────────────────────────────────────────────
  events: {
    title: 'Events',
    what: 'Manage all church events — worship services, community events, conferences, and small group gatherings.',
    howTo: [
      'Create an event with date, time, location, and description.',
      'Add registration to track attendance and collect RSVPs.',
      'Enable paid registration and set ticket tiers (Free, Fixed Price, Pay What You Can).',
      'Use the calendar view to see all events across the month.',
      'Publish events to the member portal for self-registration.',
    ],
    proTip: 'Events with photos and detailed descriptions get 3× more registrations from the portal. Always upload a header image.',
    support: true,
  },
  calendar: {
    title: 'Church Calendar',
    what: 'Full calendar view of all events, services, and room bookings across all campuses.',
    howTo: [
      'Switch between Month, Week, and Day views using the top controls.',
      'Click on any day to create a new event.',
      'Click an existing event to view or edit it.',
      'Color-coding shows event types (services, community events, groups, etc.).',
      'Drag events to reschedule them (admins only).',
    ],
    proTip: 'Share the public calendar URL with your congregation — it syncs to Google Calendar and Apple Calendar automatically.',
    support: true,
  },

  // ── Communications ────────────────────────────────────────────────
  communications: {
    title: 'Communications',
    what: 'Send emails, SMS messages, and push notifications to members, groups, or custom segments.',
    howTo: [
      'Create a new communication and select the audience (All Members, a Group, or a custom list).',
      'Choose Email, SMS, or Push Notification as the channel.',
      'Use merge fields like {{first_name}} to personalize messages.',
      'Preview your message before sending.',
      'Schedule a send time or send immediately.',
    ],
    proTip: 'Sunday evening recap emails with giving highlights and attendance stats consistently achieve 60%+ open rates.',
    support: true,
  },

  // ── God Mode ──────────────────────────────────────────────────────
  godMode: {
    title: 'God Mode — Platform Admin',
    what: 'Platform-wide view for Solomon AI administrators. See all churches, revenue, transactions, and platform health.',
    howTo: [
      'The Executive tab shows total platform MRR, church count, and transaction volume.',
      'The Churches tab lists every church with their subscription status and giving volume.',
      'The Revenue tab shows the 12-month platform revenue trend.',
      'The Support tab tracks open tickets and escalations.',
      'The Transactions tab shows all platform-wide Solomon Pay transactions.',
    ],
    proTip: 'Sort churches by "MRR" to identify your highest-value accounts for proactive success outreach.',
    support: false,
  },

  // ── Pathway Tracking ──────────────────────────────────────────────
  pathways: {
    title: 'Pathways (Discipleship)',
    what: "Track each person\'s spiritual journey and growth steps through customizable pathway stages.",
    howTo: [
      'Create pathway stages (e.g., Visitor → Attender → Member → Serving → Leading).',
      'Assign people to stages manually or via automated workflow triggers.',
      'View the discipleship funnel chart to see congregation growth distribution.',
      'Set stage-completion criteria and milestone actions (send welcome email, assign to group, etc.).',
    ],
    proTip: 'Churches with visible discipleship pathways see 28% higher volunteer retention over 12 months.',
    support: true,
  },

  // ── Reports ───────────────────────────────────────────────────────
  reports: {
    title: 'Reports',
    what: 'Pre-built and custom reports for giving, attendance, people, and more.',
    howTo: [
      'Select a report type from the sidebar.',
      'Set date ranges and filter criteria.',
      'Click "Export CSV" to download for Excel or Google Sheets.',
      'Save custom reports for quick access later.',
      'Share report links with leadership team members.',
    ],
    proTip: 'The "Lapsed Donors" report (no giving in 90+ days) is one of the highest-ROI reports — a personal outreach call restores 30-40% of lapsed donors.',
    support: true,
  },

  // ── Settings ──────────────────────────────────────────────────────
  settings: {
    title: 'Church Settings',
    what: 'Configure your church profile, branding, integrations, and platform-wide preferences.',
    howTo: [
      'Update your church name, logo, and contact information in the General tab.',
      'Configure Solomon Pay fee settings and payout schedule in the Payments tab.',
      'Manage team member roles and permissions in the Team tab.',
      'Connect integrations (Twilio SMS, Resend Email) in the Integrations tab.',
      'Set up custom fields for People in the Custom Fields tab.',
    ],
    proTip: 'Upload a high-resolution church logo (at least 500×200px) — it appears on member portal, giving receipts, and tax statements.',
    support: true,
  },

  // ── Cafe & Merch ──────────────────────────────────────────────────
  cafe: {
    title: 'Cafe Point of Sale',
    what: 'Run your church café, coffee bar, or bookstore with a simple POS system integrated with Solomon Pay.',
    howTo: [
      'Add items to the cart by clicking menu items.',
      'Apply discounts or member rates using the discount button.',
      'Select payment method: card on file, guest card entry, or cash.',
      'Transactions are recorded in the Commerce section of Solomon Pay.',
      'View daily sales summary in the Cafe Reports tab.',
    ],
    proTip: 'Integrate the Giving Round-Up feature — after a purchase, prompt "Round up to $X and donate the difference?" — it adds $8-12/week per regular café customer.',
    support: true,
  },
  merch: {
    title: 'Merch Store',
    what: 'Sell church merchandise, books, resources, and branded items from your church store.',
    howTo: [
      'Add products with photos, prices, inventory counts, and sizes/variants.',
      'Members can browse and purchase from the member portal.',
      'Process in-person orders from the Admin Merch dashboard.',
      'Track inventory levels — low stock alerts appear on the dashboard.',
    ],
    proTip: 'Seasonal items (Christmas, Easter, church anniversary merch) sell out fastest. Pre-sell with a 2-week lead time to avoid inventory risk.',
    support: true,
  },

  // ── Academy ───────────────────────────────────────────────────────
  academy: {
    title: 'Solomon Academy',
    what: 'Volunteer and leadership training platform built into Solomon AI — courses, progress tracking, and certification.',
    howTo: [
      'Assign courses to volunteers from the People profile or the Academy tab.',
      'Members access Academy from their portal under "Learn".',
      'Track course completion rates across your team.',
      'Create custom courses with video, text, and quiz modules.',
    ],
    proTip: 'Require new volunteers to complete the Safety and Security courses before their first service date.',
    support: true,
  },

  // ── Solomon AI ────────────────────────────────────────────────────
  askSolomon: {
    title: 'Ask Solomon',
    what: 'Your AI-powered church management assistant. Ask questions, get insights, and take actions across the platform.',
    howTo: [
      'Click the Solomon chat icon (bottom right) to open the assistant.',
      'Ask natural language questions: "How much did we give last month?" or "Who are our top donors?"',
      'Solomon can take actions: "Create an event for Sunday at 9am" or "Send a message to the youth group".',
      'Use voice mode for hands-free operation during services.',
      'Solomon remembers context within a conversation — you can ask follow-up questions.',
    ],
    proTip: "Say 'Solomon, summarize this week\'s giving and attendance' every Monday morning for a quick leadership briefing.",
    support: true,
  },

  // ── Additional pages ──────────────────────────────────────────
  people: {
    title: 'People',
    what: 'Your church directory. Every person who has ever been part of your church lives here.',
    howTo: [
      'Use the search bar to find anyone by name, email, or phone.',
      'Filter by membership status (Member, Visitor, Inactive) using the dropdown.',
      'Click any person to open their full profile — giving history, groups, notes, and more.',
      'Select multiple people with checkboxes to bulk-update status, send email, or export.',
      'Click + Add Person to manually add a new contact.',
    ],
    proTip: 'Use Smart Lists to create saved filters like "New this month" or "Lapsed donors" — these update automatically.',
    support: true,
  },
  households: {
    title: 'Households',
    what: 'Families grouped together under one roof. One address, one record, one family.',
    howTo: [
      'Create a household and assign a Head of Household.',
      'Add family members — Spouse, Children, Others — to the same household.',
      'Giving from all family members rolls up for combined tax statements.',
      'Update the address once to update for the entire family.',
    ],
    proTip: 'Households with assigned roles get 28% fewer duplicate entries over time. Set them up early.',
    support: true,
  },
  workflows: {
    title: 'Workflows',
    what: 'Automated care steps that follow up with people so nobody falls through the cracks.',
    howTo: [
      'Choose a trigger — new member, first donation, missed attendance, birthday, etc.',
      'Add actions — send email, add to group, assign a task, update a field.',
      'Add conditions to branch based on what happens.',
      'Activate the workflow and it runs automatically every 15 minutes.',
    ],
    proTip: 'Start with a "New Visitor Follow-Up" workflow — send a welcome email 24 hours after first check-in. It converts 40% more visitors into regulars.',
    support: true,
  },
  volunteers: {
    title: 'Volunteers',
    what: 'Everyone who serves your church — their schedules, hours, and ministry categories.',
    howTo: [
      'Browse volunteer teams and assignments.',
      'Assign people to positions on service plans.',
      'Track serving hours per ministry area.',
      "Set blackout dates so volunteers aren't scheduled when unavailable.",
    ],
    proTip: 'Volunteers who receive a personal thank-you within 48 hours of serving are 60% more likely to serve again.',
    support: true,
  },
  prayers: {
    title: 'Prayer Wall',
    what: 'Share requests and pray for each other. A living, breathing prayer community.',
    howTo: [
      'Browse the prayer wall to see requests from your community.',
      'Click the Pray button to show your support.',
      'Submit your own request — choose public or private.',
      'Prayer requests auto-expire after 30 days unless renewed.',
    ],
    proTip: 'Churches with active prayer walls report 35% higher member satisfaction and sense of community.',
    support: true,
  },
  merch_admin: {
    title: 'Merch Store',
    what: 'Your church store — apparel, books, accessories. Members browse and purchase from their portal.',
    howTo: [
      'Add products with name, price, category, and photos.',
      'Set inventory counts — low-stock alerts appear on the dashboard.',
      'Members purchase from /portal/merch with their saved payment method.',
      'View all orders in the Merch admin panel.',
    ],
    proTip: 'Limited-edition seasonal items (Christmas, Easter, anniversary) sell out fastest. Use countdown messaging.',
    support: true,
  },
  pathways_admin: {
    title: 'Pathways & Academy',
    what: "Your church's learning platform. Courses, lessons, progress tracking, and discipleship journeys.",
    howTo: [
      'Create pathway stages (Visitor → Member → Serving → Leading).',
      'Assign people to stages manually or via workflow triggers.',
      'Create courses with video, text, and quiz modules.',
      'Track completion rates and send certificates.',
    ],
    proTip: 'Requiring new volunteers to complete a safety course before their first service reduces incidents by 80%.',
    support: true,
  },
  smart_lists: {
    title: 'Smart Lists',
    what: 'Dynamic lists that update automatically based on criteria you define.',
    howTo: [
      'Click New Smart List and choose your data source (People, Donors, Attendees).',
      'Add filters — status, campus, giving range, last attendance date, etc.',
      'Save the list — it refreshes every time you open it.',
      'Use Smart Lists as audience segments in Communications.',
    ],
    proTip: 'Create a "At Risk" list: Members with zero attendance in 60 days AND zero giving in 90 days. This is your highest-ROI outreach target.',
    support: true,
  },
  audit_log: {
    title: 'Audit Log',
    what: 'Complete record of every action taken in your Solomon AI account. Who did what, and when.',
    howTo: [
      'Browse the timeline of all admin actions.',
      'Filter by user, category, or date range.',
      'Export to CSV for compliance records.',
      'All sensitive actions (edits, deletes, logins) are logged automatically.',
    ],
    proTip: "Review the audit log monthly as a healthy accountability practice. It's also required for most denominational compliance standards.",
    support: false,
  },
};
