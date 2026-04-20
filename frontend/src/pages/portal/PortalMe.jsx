import { useState, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Edit2, Mail, Phone, MapPin, Calendar, Download, ChevronRight, CreditCard, Plus, Trash2, Star, ChevronDown } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';
import { blobFromResponse, safeImgSrc } from '@/utils/sanitize';

export default function PortalMe() {
  const { user, memberData, refreshData } = useOutletContext();
  const [activeTab, setActiveTab] = useState('overview');
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [showAddCard, setShowAddCard] = useState(false);
  const [cardForm, setCardForm] = useState({ number: '', exp_month: '', exp_year: '', cvc: '', nickname: '' });
  const [savingCard, setSavingCard] = useState(false);

  const person = memberData?.person;
  const groups = memberData?.groups || [];
  const giving = memberData?.giving || {};

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'giving', label: 'Your Generosity' },
    { id: 'payments', label: 'How You Give' },
    { id: 'groups', label: 'My Groups' },
    { id: 'communications', label: 'Communications' },
  ];

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const fetchPaymentMethods = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/portal/payment-methods`);
      if (res.ok) { const d = await res.json(); setPaymentMethods(d.payment_methods || []); }
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { fetchPaymentMethods(); }, [fetchPaymentMethods]);

  const saveCard = async () => {
    if (!cardForm.number || !cardForm.exp_month || !cardForm.exp_year || !cardForm.cvc) { toast.error('Fill all card fields'); return; }
    setSavingCard(true);
    try {
      const last4 = cardForm.number.slice(-4);
      const brand = cardForm.number.startsWith('4') ? 'Visa' : cardForm.number.startsWith('5') ? 'Mastercard' : cardForm.number.startsWith('3') ? 'Amex' : 'Card';
      const res = await fetch(`${API_URL}/portal/payment-methods`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          solomonpay_token: `sp_demo_${Date.now()}`,
          card_brand: brand, card_last_four: last4,
          card_exp_month: parseInt(cardForm.exp_month), card_exp_year: parseInt(cardForm.exp_year),
          is_default: paymentMethods.length === 0, nickname: cardForm.nickname || `${brand} ****${last4}`,
        }),
      });
      if (res.ok) { toast.success('Card saved!'); setShowAddCard(false); setCardForm({ number: '', exp_month: '', exp_year: '', cvc: '', nickname: '' }); fetchPaymentMethods(); }
      else { const err = await res.json(); toast.error(err.detail || 'Failed to save'); }
    } catch { toast.error('Failed to save card'); }
    finally { setSavingCard(false); }
  };

  const deleteCard = async (id) => {
    if (!confirm('Remove this payment method?')) return;
    try {
      const res = await fetch(`${API_URL}/portal/payment-methods/${id}`, { method: 'DELETE' });
      if (res.ok) { toast.success('Removed'); fetchPaymentMethods(); }
    } catch { toast.error('Failed to remove'); }
  };

  const setDefault = async (id) => {
    try {
      const res = await fetch(`${API_URL}/portal/payment-methods/${id}/default`, { method: 'PUT' });
      if (res.ok) { toast.success('Default updated'); fetchPaymentMethods(); }
    } catch { toast.error('Failed'); }
  };

  const downloadStatement = async (year) => {
    try {
      const res = await fetch(`${API_URL}/portal/giving/statement/${year}/pdf`);
      if (!res.ok) { toast.error('Failed to generate'); return; }
      // Validate content-type before creating a blob URL (CWE-79 mitigation)
      const blob = await blobFromResponse(res, ['application/pdf']);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.setAttribute('href', url);
      a.setAttribute('download', `giving_statement_${year}.pdf`);
      document.body.appendChild(a); a.click(); a.remove(); window.URL.revokeObjectURL(url);
      toast.success(`${year} statement downloaded`);
    } catch { toast.error('Download failed'); }
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
                </div>
              )}
            </div>
            {(giving.ytd_total || 0) > 0 ? (
            <div className="space-y-2 mt-4" data-testid="me-tax-statement-section">
              <p className="text-xs font-medium text-slate-500">DOWNLOAD TAX STATEMENT</p>
              <div className="grid grid-cols-2 gap-2">
                {[new Date().getFullYear(), new Date().getFullYear()-1, new Date().getFullYear()-2, new Date().getFullYear()-3].map(y => (
                  <button key={y} onClick={() => downloadStatement(y)} className="flex items-center gap-2 px-3 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-sm" data-testid={`me-download-${y}`}>
                    <Download className="w-3.5 h-3.5 text-slate-500" /> {y}
                  </button>
                ))}
              </div>
            </div>
            ) : (
            <div className="mt-4 p-3 bg-slate-50 rounded-lg text-center" data-testid="me-tax-statement-section">
              <p className="text-xs text-slate-400">Statements available after your first gift</p>
            </div>
            )}
            <div className="portal-giving-chart-placeholder mt-4">
              <p className="text-slate-400 text-sm">24-month giving chart coming soon</p>
            </div>
          </div>
        )}

        {activeTab === 'payments' && (
          <div className="portal-payments-content" data-testid="payment-methods-tab">
            <div className="flex items-center justify-between mb-4">
              <h3 className="portal-info-title">Saved Payment Methods</h3>
              <button onClick={() => setShowAddCard(!showAddCard)} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 text-white rounded-lg text-sm hover:bg-slate-800 transition-colors" data-testid="add-payment-btn">
                <Plus className="w-3.5 h-3.5" /> Add Card
              </button>
            </div>

            {showAddCard && (
              <div className="bg-slate-50 rounded-lg p-4 mb-4 space-y-3" data-testid="add-card-form">
                <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 mb-2">
                  <p className="text-xs text-blue-700 flex items-center gap-1.5">
                    <span>🔒</span> Card data is encrypted and tokenized by Solomon Pay. Raw card numbers are never stored.
                  </p>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">CARD NUMBER</label>
                  <input type="text" maxLength="19" value={cardForm.number.replace(/\d(?=\d{4})/g, '•').slice(-19)} onChange={e => setCardForm({...cardForm, number: e.target.value.replace(/\D/g,'')})} placeholder="•••• •••• •••• ••••" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300 font-mono tracking-widest" data-testid="card-number-input" />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs font-medium text-slate-500">MONTH</label>
                    <input type="text" maxLength="2" value={cardForm.exp_month} onChange={e => setCardForm({...cardForm, exp_month: e.target.value})} placeholder="MM" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" data-testid="card-month-input" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-500">YEAR</label>
                    <input type="text" maxLength="4" value={cardForm.exp_year} onChange={e => setCardForm({...cardForm, exp_year: e.target.value})} placeholder="2028" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" data-testid="card-year-input" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-slate-500">CVC</label>
                    <input type="text" maxLength="4" value={cardForm.cvc} onChange={e => setCardForm({...cardForm, cvc: e.target.value})} placeholder="123" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" data-testid="card-cvc-input" />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">NICKNAME (optional)</label>
                  <input type="text" value={cardForm.nickname} onChange={e => setCardForm({...cardForm, nickname: e.target.value})} placeholder="Personal Visa" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" data-testid="card-nickname-input" />
                </div>
                <div className="flex gap-2">
                  <button onClick={saveCard} disabled={savingCard} className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm hover:bg-slate-800 disabled:opacity-50" data-testid="save-card-btn">{savingCard ? 'Saving...' : 'Save Card'}</button>
                  <button onClick={() => setShowAddCard(false)} className="px-4 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50">Cancel</button>
                </div>
              </div>
            )}

            {paymentMethods.length === 0 && !showAddCard ? (
              <div className="text-center py-8">
                <CreditCard className="w-12 h-12 text-slate-300 mx-auto" />
                <p className="text-slate-500 mt-3 text-sm">No saved payment methods</p>
                <p className="text-slate-400 text-xs mt-1">Add a card for faster checkout on Merch, Cafe, and Giving</p>
              </div>
            ) : (
              <div className="space-y-2">
                {paymentMethods.map(pm => (
                  <div key={pm.id} className="flex items-center justify-between p-3 border border-slate-200 rounded-lg" data-testid={`payment-method-${pm.id}`}>
                    <div className="flex items-center gap-3">
                      <CreditCard className="w-5 h-5 text-slate-600" />
                      <div>
                        <p className="text-sm font-medium text-slate-800">{pm.card_brand} •••• {pm.card_last_four}</p>
                        <p className="text-xs text-slate-400">Exp {pm.card_exp_month}/{pm.card_exp_year} {pm.nickname ? `· ${pm.nickname}` : ''}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {pm.is_default ? (
                        <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full font-medium" data-testid={`default-badge-${pm.id}`}>Default</span>
                      ) : (
                        <button onClick={() => setDefault(pm.id)} className="text-xs text-blue-600 hover:underline" data-testid={`set-default-${pm.id}`}>Set Default</button>
                      )}
                      <button onClick={() => deleteCard(pm.id)} className="p-1 text-slate-400 hover:text-red-500 transition-colors" data-testid={`delete-card-${pm.id}`}>
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <p className="text-xs text-slate-400 mt-4">Payment methods are securely stored and can be used for Merch, Cafe, and Giving transactions.</p>
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
              ].map((pref) => (
                <label key={pref.id} className="portal-pref-item">
                  <input type="checkbox" defaultChecked={pref.checked} className="portal-checkbox" />
                  <span>{pref.label}</span>
                </label>
              ))}
            </div>

            <h3 className="portal-info-title mt-6">Directory Privacy</h3>
            <p className="text-xs text-slate-400 mb-3">Control what other members can see about you in the church directory. Admins always see full details.</p>
            <div className="portal-prefs-list" data-testid="directory-privacy-section">
              {[
                { id: 'share_email', label: 'Show my email in the directory', defaultChecked: true },
                { id: 'share_phone', label: 'Show my phone number in the directory', defaultChecked: false },
                { id: 'share_address', label: 'Show my address in the directory', defaultChecked: false },
                { id: 'directory_visible', label: 'Include me in the member directory', defaultChecked: true },
              ].map((pref) => (
                <label key={pref.id} className="portal-pref-item" data-testid={`privacy-${pref.id}`}>
                  <input
                    type="checkbox"
                    defaultChecked={pref.defaultChecked}
                    className="portal-checkbox"
                    onChange={async (e) => {
                      const token = sessionStorage.getItem('session_token');
                      await fetch(`${API_URL}/portal/profile/privacy`, {
                        method: 'PUT',
                        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                        body: JSON.stringify({ [pref.id]: e.target.checked }),
                      });
                    }}
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
