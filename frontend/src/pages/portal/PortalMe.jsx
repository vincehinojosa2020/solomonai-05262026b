import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Edit2, Mail, Phone, MapPin, Calendar, Download, ChevronRight } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { API_URL, formatCurrency } from '@/lib/utils';

export default function PortalMe() {
  const { user, memberData, refreshData } = useOutletContext();
  const [activeTab, setActiveTab] = useState('overview');

  const person = memberData?.person;
  const groups = memberData?.groups || [];
  const giving = memberData?.giving || {};

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'giving', label: 'My Giving' },
    { id: 'groups', label: 'My Groups' },
    { id: 'communications', label: 'Communications' },
  ];

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const formatMemberSince = () => {
    const date = memberData?.member_since || person?.membership_date;
    if (!date) return 'Member';
    const d = new Date(date);
    return `Member since ${d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}`;
  };

  return (
    <div className="portal-me" data-testid="portal-me">
      {/* Profile Header */}
      <div className="portal-profile-header">
        <Avatar className="w-24 h-24 border-4 border-white shadow-lg">
          <AvatarImage src={user?.picture || person?.photo_url} />
          <AvatarFallback className="bg-teal-500 text-white text-2xl font-semibold">
            {getInitials(user?.name)}
          </AvatarFallback>
        </Avatar>
        <h1 className="portal-profile-name">{user?.name}</h1>
        <p className="portal-profile-since">{formatMemberSince()}</p>
        <button className="portal-edit-profile-btn">
          <Edit2 className="w-4 h-4" />
          Edit Profile
        </button>
      </div>

      {/* Tabs */}
      <div className="portal-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`portal-tab ${activeTab === tab.id ? 'active' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="portal-tab-content">
        {activeTab === 'overview' && (
          <div className="portal-overview-content">
            {/* Personal Info */}
            <div className="portal-info-section">
              <h3 className="portal-info-title">Personal Information</h3>
              <div className="portal-info-grid">
                <div className="portal-info-item">
                  <Mail className="w-4 h-4 text-slate-400" />
                  <div>
                    <span className="portal-info-label">Email</span>
                    <span className="portal-info-value">{user?.email}</span>
                  </div>
                </div>
                {person?.mobile_phone && (
                  <div className="portal-info-item">
                    <Phone className="w-4 h-4 text-slate-400" />
                    <div>
                      <span className="portal-info-label">Mobile</span>
                      <span className="portal-info-value">{person.mobile_phone}</span>
                    </div>
                  </div>
                )}
                {person?.campus && (
                  <div className="portal-info-item">
                    <MapPin className="w-4 h-4 text-slate-400" />
                    <div>
                      <span className="portal-info-label">Campus</span>
                      <span className="portal-info-value">{person.campus}</span>
                    </div>
                  </div>
                )}
                {person?.date_of_birth && (
                  <div className="portal-info-item">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <div>
                      <span className="portal-info-label">Birthday</span>
                      <span className="portal-info-value">
                        {new Date(person.date_of_birth).toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Engagement Card */}
            <div className="portal-engagement-card">
              <h3 className="portal-info-title">Engagement</h3>
              <div className="portal-engagement-stats">
                <div className="portal-engagement-stat">
                  <span className="portal-engagement-value">7 of 7</span>
                  <span className="portal-engagement-label">Sundays this year</span>
                </div>
                <div className="portal-engagement-stat">
                  <span className="portal-engagement-value">14 mo</span>
                  <span className="portal-engagement-label">Giving streak</span>
                </div>
                <div className="portal-engagement-stat">
                  <span className="portal-engagement-value">{groups.length}</span>
                  <span className="portal-engagement-label">Active groups</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'giving' && (
          <div className="portal-giving-content">
            <div className="portal-giving-summary">
              <div className="portal-giving-ytd">
                <span className="portal-giving-ytd-label">YTD Total</span>
                <span className="portal-giving-ytd-value">{formatCurrency(giving.ytd_total || 0)}</span>
              </div>
              
              {giving.recurring && (
                <div className="portal-recurring-info">
                  <span>Recurring: {formatCurrency(giving.recurring.amount)}/{giving.recurring.frequency}</span>
                  <button className="text-blue-600 text-sm hover:underline">Edit</button>
                  <button className="text-red-600 text-sm hover:underline">Cancel</button>
                </div>
              )}
            </div>

            <button className="portal-download-statement-btn">
              <Download className="w-4 h-4" />
              Download Year-End Statement
            </button>

            {/* Mini Chart Placeholder */}
            <div className="portal-giving-chart-placeholder">
              <p className="text-slate-400 text-sm">24-month giving chart coming soon</p>
            </div>
          </div>
        )}

        {activeTab === 'groups' && (
          <div className="portal-groups-content">
            {groups.length === 0 ? (
              <p className="text-slate-500 text-sm py-4">You're not currently in any groups.</p>
            ) : (
              <div className="portal-my-groups-list">
                {groups.map((group) => (
                  <div key={group.id} className="portal-my-group-item">
                    <div>
                      <h4 className="portal-my-group-name">{group.name}</h4>
                      <p className="portal-my-group-meta">{group.meeting_day}s at {group.meeting_time}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                  </div>
                ))}
              </div>
            )}
            <a href="/portal/groups" className="portal-discover-groups-link">
              Discover more groups →
            </a>
          </div>
        )}

        {activeTab === 'communications' && (
          <div className="portal-communications-content">
            <h3 className="portal-info-title">Email Preferences</h3>
            <div className="portal-prefs-list">
              {[
                { id: 'newsletter', label: 'Weekly newsletter', checked: true },
                { id: 'events', label: 'Event reminders', checked: true },
                { id: 'receipts', label: 'Giving receipts', checked: true },
                { id: 'groups', label: 'Group updates', checked: true },
                { id: 'prayer', label: 'Prayer requests', checked: false },
              ].map((pref) => (
                <label key={pref.id} className="portal-pref-item">
                  <input
                    type="checkbox"
                    defaultChecked={pref.checked}
                    className="portal-checkbox"
                  />
                  <span>{pref.label}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
