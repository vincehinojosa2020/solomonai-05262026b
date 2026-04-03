import { useState } from 'react';
import { ChevronDown, ChevronUp, Lightbulb, ArrowRight, X } from 'lucide-react';

const PAGE_EDUCATION = {
  giving: {
    what: 'Stewardship is where giving happens — track donations, manage funds, set goals, and run giving reports.',
    why: 'Visibility into your giving data drives better stewardship culture and helps leadership make informed budget decisions.',
    cta: 'Record your first gift',
    ctaAction: null,
  },
  people: {
    what: 'Your church directory — every member, visitor, and contact in one searchable, filterable database.',
    why: 'Knowing your people by name, history, and engagement level is the foundation of real pastoral care.',
    cta: 'Add a new member',
    ctaAction: null,
  },
  services: {
    what: 'Plan every element of your worship service — songs, message, team, transitions — from start to finish.',
    why: 'A well-planned service replaces scattered spreadsheets and group texts, and lets your whole team stay in sync.',
    cta: 'Create your first service plan',
    ctaAction: null,
  },
  groups: {
    what: 'Manage small groups, Bible studies, ministry teams, and any gathering of people in your church.',
    why: 'Churches where 40%+ of members are in groups have 3× higher retention and 2.9× higher giving per person.',
    cta: 'Create a group',
    ctaAction: null,
  },
  events: {
    what: 'Create and manage church events — from weekly services to major conferences and community outreach.',
    why: 'Well-managed events with online registration convert visitors to regular attenders at a 40% higher rate.',
    cta: 'Create an event',
    ctaAction: null,
  },
  checkin: {
    what: 'Secure, code-based check-in for kids ministry. Every child gets a unique pickup code every service.',
    why: 'A secure check-in system is the #1 trust signal for young families deciding whether to come back.',
    cta: 'Set up your first classroom',
    ctaAction: null,
  },
  communications: {
    what: 'Send emails, SMS, and push notifications to your entire congregation or specific segments.',
    why: 'Churches with consistent weekly communication see 35% higher giving and 28% higher event attendance.',
    cta: 'Compose your first message',
    ctaAction: null,
  },
  reports: {
    what: 'Data-driven insights across every area of your church — giving, attendance, groups, and more.',
    why: 'You can\'t lead what you can\'t see. Regular reporting helps leadership make decisions based on reality, not intuition.',
    cta: 'View your Giving report',
    ctaAction: null,
  },
  calendar: {
    what: 'Full calendar view of all events, services, room bookings, and group meetings across your church.',
    why: 'A shared calendar eliminates scheduling conflicts and ensures your whole team knows what\'s coming.',
    cta: 'Create an event',
    ctaAction: null,
  },
  solomonpay: {
    what: 'Solomon Pay is your built-in payment processor — no third-party accounts, no monthly fees, just processing costs.',
    why: 'Every dollar your church saves on payment processing fees is a dollar that stays in ministry.',
    cta: 'View your giving dashboard',
    ctaAction: null,
  },
};

/**
 * FeatureEducationHeader — collapsible education banner for every page.
 * 
 * Usage: <FeatureEducationHeader featureKey="giving" />
 */
export function FeatureEducationHeader({ featureKey, customContent }) {
  const storageKey = `edu_dismissed_${featureKey}`;
  const [visible, setVisible] = useState(!localStorage.getItem(storageKey));
  const [expanded, setExpanded] = useState(false);

  const content = customContent || PAGE_EDUCATION[featureKey];
  if (!content) return null;
  if (!visible) return null;

  return (
    <div className="bg-gradient-to-r from-blue-50 to-slate-50 border border-blue-200 rounded-xl overflow-hidden mb-4" data-testid={`edu-header-${featureKey}`}>
      <div className="px-4 py-3 flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <div className="w-7 h-7 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
            <Lightbulb className="w-4 h-4 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-blue-900">{content.what}</p>
            {expanded && (
              <div className="mt-2 space-y-2">
                <p className="text-sm text-blue-700">
                  <span className="font-medium">Why it matters: </span>{content.why}
                </p>
                {content.cta && (
                  <button
                    onClick={() => { if (content.ctaAction) content.ctaAction(); }}
                    className="inline-flex items-center gap-1 text-sm font-medium text-blue-700 hover:text-blue-900"
                    data-testid={`edu-cta-${featureKey}`}
                  >
                    {content.cta} <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1 ml-3 flex-shrink-0">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-blue-400 hover:text-blue-700 transition-colors p-1"
            title={expanded ? 'Show less' : 'Learn more'}
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          <button
            onClick={() => { localStorage.setItem(storageKey, '1'); setVisible(false); }}
            className="text-blue-300 hover:text-blue-500 transition-colors p-1"
            title="Dismiss"
            data-testid={`edu-dismiss-${featureKey}`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
