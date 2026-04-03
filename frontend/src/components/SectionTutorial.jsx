import { useState } from 'react';
import { HelpCircle, X } from 'lucide-react';
import { Button } from '../components/ui/button';

export const SectionTutorial = ({ title, sections, tip }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!isOpen) {
    return (
      <Button variant="outline" size="sm" onClick={() => setIsOpen(true)} data-testid="how-it-works-btn">
        <HelpCircle className="w-4 h-4 mr-1.5" /> How It Works
      </Button>
    );
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 space-y-3" data-testid="how-it-works-panel">
      <div className="flex items-start justify-between">
        <h3 className="text-sm font-semibold text-blue-900 flex items-center gap-2">
          <HelpCircle className="w-4 h-4" /> {title}
        </h3>
        <button onClick={() => setIsOpen(false)} className="text-blue-400 hover:text-blue-600">
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-blue-900">
        {sections.map((section, idx) => (
          <div key={`step-${idx}`}>
            <p className="font-semibold mb-0.5">{idx + 1}. {section.title}</p>
            <p className="text-blue-700 text-xs leading-relaxed">{section.body}</p>
          </div>
        ))}
      </div>
      {tip && (
        <div className="pt-2 border-t border-blue-200">
          <p className="text-xs text-blue-600"><strong>Tip:</strong> {tip}</p>
        </div>
      )}
    </div>
  );
};

// Pre-built tutorials for each section
export const TUTORIALS = {
  groups: {
    title: 'How Groups Work',
    sections: [
      { title: 'Create a Group', body: 'Click "Create Group" and set the name, type, schedule, and whether it\'s open or request-only. Groups can be Small Groups, Ministry Teams, Classes, or Custom.' },
      { title: 'Add Members', body: 'Open any group and click "Add Member" to assign people. Members can also request to join from the Member Portal — you\'ll see pending requests to approve.' },
      { title: 'Track Attendance', body: 'Use the attendance tab inside each group to record who showed up at meetings. Solomon AI will automatically flag "at-risk" members who haven\'t attended recently.' },
      { title: 'Group Communication', body: 'Send messages to your entire group from the Messages tab. Members see these in their portal. You can also schedule group events with RSVP tracking.' },
    ],
    tip: 'Members can discover and join open groups from their portal. For private groups, set them to "request-only" and approve members manually.',
  },
  events: {
    title: 'How Events Work',
    sections: [
      { title: 'Create an Event', body: 'Click "Create Event" to set the title, date/time, location, and capacity. You can make events free or paid, and enable waitlisting when full.' },
      { title: 'Registration', body: 'Members register from their portal. You\'ll see registrations, check-ins, and waitlist status in real time. Add promo codes for discounted or free tickets.' },
      { title: 'Room Booking', body: 'Use the Calendar tab to book rooms for your event. Solomon AI auto-detects conflicts so you never double-book a space.' },
      { title: 'Day-of Management', body: 'On event day, use check-in to track attendance. View reports afterward to see registration-to-attendance ratios and engagement data.' },
    ],
    tip: 'Add recurring events (like weekly Bible study) by setting a recurrence pattern. Each instance tracks its own registrations.',
  },
  checkins: {
    title: 'How Kids Check-In Works',
    sections: [
      { title: 'Set Up Locations', body: 'Create check-in locations (Main Campus, West Campus) and stations (Nursery, Preschool, Elementary). Each station has a grade range and capacity limit.' },
      { title: 'Register Children', body: 'Parents add their children in the Member Portal under "Kids" or you can add them in the admin. Set medical alerts, allergies, and authorized pickups.' },
      { title: 'Check In', body: 'Parents self-check-in from their phone or use a kiosk station. A unique pickup code is generated for each child — this code is required for checkout.' },
      { title: 'Security & Labels', body: 'Medical alerts appear prominently for volunteers. Labels can be printed with the child\'s name, classroom, and pickup code. Guardian PINs add an extra security layer.' },
    ],
    tip: 'Solomon AI can check in children via voice: "Check in Emma for Sunday School." The pickup code is automatically generated and shown in the chat.',
  },
  giving: {
    title: 'How Giving Works',
    sections: [
      { title: 'Fund Management', body: 'Create funds (General, Missions, Building) in Solomon Pay Admin > Funds tab. Set goals and track progress. Funds appear as options when members give.' },
      { title: 'Member Giving', body: 'Members give from their portal or via Solomon AI voice. They can make one-time gifts or set up recurring giving (weekly, biweekly, monthly). Donor-covered fees are optional.' },
      { title: 'Solomon Pay Dashboard', body: 'View all transactions, donor insights (DonorIQ), payouts, and reports from the Solomon Pay Admin page. Export to CSV for your records.' },
      { title: 'Tax Statements', body: 'Generate year-end giving statements for all donors at once from the Statements tab. Members can also download their own PDF statements from their portal.' },
    ],
    tip: 'DonorIQ automatically classifies your donors into engagement stages: New, Occasional, Regular, Recurring, At-Risk, and Lapsed. Use this to identify who needs follow-up.',
  },
  people: {
    title: 'How People Management Works',
    sections: [
      { title: 'Member Directory', body: 'View all members, filter by status, campus, or custom tags. Click any person to see their full profile: contact info, giving history, group memberships, and check-in records.' },
      { title: 'Households', body: 'Link family members into households. This helps with communication (send one email per household), giving statements, and kids check-in (authorized pickups).' },
      { title: 'Smart Lists', body: 'Create dynamic lists based on criteria: "All members who gave in the last 90 days" or "Parents with kids under 5." These update automatically as data changes.' },
      { title: 'Workflows', body: 'Automate follow-up processes: new visitor follow-up, membership class enrollment, volunteer onboarding. Each step has an owner and due date.' },
    ],
    tip: 'Use the Duplicates tool to find and merge duplicate records. Solomon AI detects potential duplicates based on name, email, and phone number matching.',
  },
  volunteers: {
    title: 'How Volunteer Scheduling Works',
    sections: [
      { title: 'Create Teams', body: 'Set up volunteer teams (Worship, A/V, Ushers, Kids Ministry). Each team has positions (Lead, Backup) and members assigned to them.' },
      { title: 'Schedule Volunteers', body: 'Assign team members to specific service dates. Drag and drop to rearrange. Solomon AI ensures no one is double-booked across teams.' },
      { title: 'Blockout Dates', body: 'Volunteers can set dates they\'re unavailable. The scheduler shows these visually so you can plan around absences.' },
      { title: 'Communication', body: 'Send schedule notifications to your teams. Volunteers see their upcoming assignments in the Member Portal and can request swaps.' },
    ],
    tip: 'Use service plan templates to pre-fill team assignments. This saves hours when your teams rotate on a predictable schedule.',
  },
  registrations: {
    title: 'How Registrations Work',
    sections: [
      { title: 'Set Up Registration', body: 'On any event, enable registration and set capacity limits. Choose if it\'s free or paid, and add custom form fields (T-shirt size, dietary needs, etc.).' },
      { title: 'Add-ons & Promo Codes', body: 'Create optional add-ons (childcare, meals) with separate pricing. Generate promo codes for discounts or free admission for volunteers.' },
      { title: 'Waitlisting', body: 'When an event reaches capacity, the waitlist kicks in automatically. Members are notified if a spot opens up. You can also manually move people off the waitlist.' },
      { title: 'Reports', body: 'View registration counts, revenue collected, and attendance rates. Export registrant lists for event planning and follow-up.' },
    ],
    tip: 'For recurring events like weekly classes, create one registration event and members sign up for the full series. Track per-session attendance separately.',
  },
  communications: {
    title: 'How Communications Work',
    sections: [
      { title: 'Email', body: 'Send emails to individuals, groups, smart lists, or your entire congregation. Use the rich text editor to format your message. Track open rates and engagement.' },
      { title: 'SMS', body: 'Send text messages for urgent announcements, event reminders, or giving campaigns. Text-to-give lets members donate by replying to a text with an amount.' },
      { title: 'History', body: 'All communications are logged — see what was sent, to whom, and when. This creates an audit trail and helps coordinate between staff members.' },
    ],
    tip: 'Schedule communications in advance — great for Sunday morning reminders sent automatically on Saturday evening.',
  },
};
